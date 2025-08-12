
import os, time, requests, tempfile, json
from flask import Flask, request, send_file, jsonify

VERTOPAL_API = "https://api.vertopal.com/v1"
APP_ID = os.getenv("e151a516-0ba1-cb61-7f05-7fc71d667d7a")
APP_TOKEN = os.getenv("rP1h79r91DO0F7UHK0Q-yWOQW3JhNRYP5ddGGoJ0TOwVudFmk2eB8BcWFBwjqpkfxMI52bh3IvTz8KZ0qsjQHKGHU4Pgh8c.c9KH-iwx-B")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB

def need_creds():
    return not (APP_ID and APP_TOKEN)

def vpost(endpoint, data=None, files=None):
    headers = {"Authorization": f"Bearer {APP_TOKEN}"}
    # Vertopal expects a 'data' form field containing JSON
    form = {"data": json.dumps(data)} if data else None
    return requests.post(f"{VERTOPAL_API}{endpoint}", headers=headers, files=files, data=form)

@app.route("/", methods=["GET"])
def index():
    cred_warning = ""
    if need_creds():
        cred_warning = "<p style='color:#b00'><strong>Missing credentials:</strong> set VERTOPAL_APP_ID and VERTOPAL_APP_TOKEN.</p>"
    return f"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>LaTeX → Word via Vertopal</title>
    <style>
      body{{font-family:system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;margin:40px}}
      .card{{max-width:720px;padding:24px;border:1px solid #eee;border-radius:16px;box-shadow:0 4px 12px rgba(0,0,0,.05)}}
      label{{display:block;margin:12px 0 6px}}
      input,button,select{{font-size:16px}}
      button{{padding:10px 16px;border-radius:12px;border:1px solid #ddd;background:#fff;cursor:pointer}}
      button:hover{{box-shadow:0 2px 6px rgba(0,0,0,.08)}}
      .muted{{color:#666}}
    </style>
  </head>
  <body>
    <div class="card">
      <h1>LaTeX → Word (.docx) Converter</h1>
      {cred_warning}
      <form action="/convert" method="post" enctype="multipart/form-data">
        <label>Upload .tex/.latex file</label>
        <input type="file" name="file" accept=".tex,.latex" required>

        <label>Output format</label>
        <select name="output">
          <option value="docx" selected>DOCX (Word)</option>
          <option value="doc">DOC (legacy Word)</option>
          <option value="pdf">PDF</option>
        </select>

        <div style="margin-top:16px">
          <button type="submit">Convert</button>
        </div>
      </form>
      <p class="muted">Powered by Vertopal API. For complex multi-file projects with images, the Pandoc self-hosted version may work better.</p>
    </div>
  </body>
</html>
"""

@app.route("/convert", methods=["POST"])
def convert():
    if need_creds():
        return jsonify(error="Server missing Vertopal credentials. Set VERTOPAL_APP_ID and VERTOPAL_APP_TOKEN."), 500

    if "file" not in request.files:
        return jsonify(error="No file uploaded"), 400
    uploaded = request.files["file"]
    output = request.form.get("output", "docx")

    # 1) Upload
    files = {"file": (uploaded.filename, uploaded.stream, uploaded.mimetype or "application/octet-stream")}
    data = {"app": APP_ID}
    r = vpost("/upload/file", data=data, files=files)
    res = r.json() if r.headers.get("content-type","").startswith("application/json") else {}
    try:
        upload_connector = res["result"]["output"]["connector"]
    except Exception:
        return jsonify(error="Upload failed", response=res, raw=r.text), 500

    # 2) Convert (ASYNC)
    convert_payload = {
        "app": APP_ID,
        "connector": upload_connector,
        "include": ["entity", "result"],
        "mode": "async",
        "parameters": {"output": output}
    }
    r2 = vpost("/convert/file", data=convert_payload)
    res2 = r2.json() if r2.headers.get("content-type","").startswith("application/json") else {}
    # prefer the returned entity id as the connector to monitor
    convert_connector = res2.get("entity", {}).get("id") or res2.get("result", {}).get("output", {}).get("connector") or upload_connector

    # 3) Poll until done (task/response)
    for _ in range(60):
        poll_payload = {"app": APP_ID, "connector": convert_connector, "parameters": {"include": ["result"]}}
        pr = vpost("/task/response", data=poll_payload)
        pres = pr.json() if pr.headers.get("content-type","").startswith("application/json") else {}
        inner = pres.get("result", {}).get("output", {}).get("result", {})
        status = inner.get("output", {}).get("status") or inner.get("status")
        if status in ("successful", "failed"):
            convert_result = inner
            break
        time.sleep(2)
    else:
        return jsonify(error="Conversion timed out. Try again."), 504

    if status != "successful":
        return jsonify(error="Conversion failed", details=convert_result), 500

    # 4) Generate download URL
    out_connector = convert_result.get("output", {}).get("connector") or convert_result.get("connector") or convert_connector
    dres = vpost("/download/url", data={"app": APP_ID, "connector": out_connector}).json()
    url_connector = dres["result"]["output"]["connector"]

    # 5) Get file content
    gr = vpost("/download/url/get", data={"app": APP_ID, "connector": url_connector})
    if gr.status_code != 200:
        return jsonify(error="Download failed", raw=gr.text), 500

    suffix = f".{output}"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(gr.content); tmp.flush(); tmp.close()
    return send_file(tmp.name, as_attachment=True, download_name=f"converted{suffix}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

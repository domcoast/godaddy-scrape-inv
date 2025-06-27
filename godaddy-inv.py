from flask import Flask, request, jsonify
import requests, zipfile, io, json

app = Flask(__name__)

GODADDY_ZIP_URL = "https://inventory.auctions.godaddy.com/all_biddable_auctions.json.zip"
N8N_WEBHOOK_URL = "https://n8n.scrapifyapi.com/webhook/godaddy-auctions-render"

@app.route('/filter-domains', methods=['POST'])
def filter_domains():
    try:
        # Step 1: Download ZIP
        response = requests.get(GODADDY_ZIP_URL)
        if response.status_code != 200:
            return jsonify({"error": "Failed to download ZIP file"}), 500

        # Step 2: Extract JSON
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            json_filename = z.namelist()[0]
            with z.open(json_filename) as f:
                full_data = json.load(f)

        all_domains = full_data.get("data", [])
        
        # Step 3: Posted domains
        input_domains = request.json.get("domains", [])
        input_domains_set = set(domain.lower() for domain in input_domains)

        # Step 4: Filter
        matched = [
            domain for domain in all_domains
            if domain.get("domainName", "").lower() in input_domains_set
        ]

        # Step 5: Send to n8n webhook
        if matched:
            try:
                requests.post(N8N_WEBHOOK_URL, json={"matched_domains": matched})
            except Exception as webhook_err:
                print(f"Webhook error: {webhook_err}")

        return jsonify(matched), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)

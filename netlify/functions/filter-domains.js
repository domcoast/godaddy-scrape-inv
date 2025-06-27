const axios = require('axios');
const AdmZip = require('adm-zip');

const GODADDY_ZIP_URL = "https://inventory.auctions.godaddy.com/all_biddable_auctions.json.zip";
const N8N_WEBHOOK_URL = "https://n8n.scrapifyapi.com/webhook/godaddy-auctions-render";

exports.handler = async (event) => {
  try {
    const body = JSON.parse(event.body || '{}');
    const inputDomains = new Set((body.domains || []).map(d => d.toLowerCase()));

    // Download and unzip JSON
    const zipRes = await axios.get(GODADDY_ZIP_URL, { responseType: 'arraybuffer' });
    const zip = new AdmZip(zipRes.data);
    const zipEntries = zip.getEntries();
    const jsonContent = JSON.parse(zipEntries[0].getData().toString('utf8'));

    const allDomains = jsonContent.data || [];

    // Filter matching domains
    const matched = allDomains.filter(domain =>
      inputDomains.has((domain.domainName || '').toLowerCase())
    );

    // Send to n8n if matched
    if (matched.length > 0) {
      try {
        await axios.post(N8N_WEBHOOK_URL, { matched_domains: matched });
      } catch (err) {
        console.error('[n8n webhook error]', err.message);
      }
    }

    return {
      statusCode: 200,
      body: JSON.stringify(matched),
      headers: { 'Content-Type': 'application/json' }
    };
  } catch (err) {
    console.error('Error:', err.message);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: err.message }),
      headers: { 'Content-Type': 'application/json' }
    };
  }
};

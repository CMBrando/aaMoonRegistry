function parseMoonScan(text) {
  const lines = text.split(/\r?\n/);
  const data = [];
  let sawHeader = false;
  let currentMoonName = null;

  for (let raw of lines) {
    const line = raw.replace(/\s+$/, ''); // trim right
    if (!line.trim()) continue;

    // Detect and skip header
    if (!sawHeader && /(^|\s)Moon\s+Product(\s|$)/i.test(line) && /^\s*Moon(\s|$)/i.test(line)) {
      sawHeader = true;
      continue;
    }

    // Moon name line (no leading whitespace)
    if (/^[^\s]/.test(line)) {
      currentMoonName = line.trim();
      continue;
    }

    // Data row
    const parts = line.trim().split(/\s{2,}|\t+/);
    if (parts.length < 6) continue;

    const [moonProduct, qtyStr, oreTypeIdStr, /* solarSystemId */, /* planetId */, moonIdStr] = parts;

    const quantity = parseFloat(qtyStr);
    const oreTypeId = parseInt(oreTypeIdStr, 10);
    const moonId = parseInt(moonIdStr, 10);

    if (
      Number.isFinite(quantity) &&
      Number.isInteger(oreTypeId) &&
      Number.isInteger(moonId) &&
      currentMoonName
    ) {
      data.push({
        moonId,
        oreTypeId,
        quantity,
        moonProduct,
        moonName: currentMoonName,
      });
    }
  }

  return data;
}
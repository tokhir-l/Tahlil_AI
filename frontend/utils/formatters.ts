/**
 * Detects if text contains a tabular structure and returns HTML table string or null
 */
export const extractTableFromText = (text: string): { tableHtml: string; explanation: string } | null => {
  const lines = text.split('\n').map(line => line.trim()).filter(line => line);
  if (lines.length < 2) return null;

  let headerLine = -1;
  let separator: string | RegExp = '';
  let dataStartIndex = -1;

  // Check for Markdown table first
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes('|') && lines[i].split('|').length >= 2) {
      // Check if next line is a separator line (e.g. ---|---)
      if (i + 1 < lines.length && lines[i + 1].includes('---')) {
         headerLine = i;
         separator = '|';
         dataStartIndex = i + 2; // Skip header and separator
         break;
      }
      // Or just a pipe separated list
      headerLine = i;
      separator = '|';
      dataStartIndex = i + 1;
      break;
    }
  }

  // Fallback to tab or double space
  if (headerLine === -1) {
     for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes('\t') && lines[i].split('\t').length >= 2) {
           headerLine = i;
           separator = '\t';
           dataStartIndex = i + 1;
           break;
        }
     }
  }

  if (headerLine === -1 || dataStartIndex === -1) return null;

  const parseRow = (line: string, sep: string | RegExp) => {
    if (sep === '|') {
        return line.split('|').map(c => c.trim()).filter(c => c.length > 0);
    }
    return line.split(sep).map(c => c.trim()).filter(c => c.length > 0);
  };

  const headers = parseRow(lines[headerLine], separator);
  const rows = [];
  
  // Collect rows
  for (let i = dataStartIndex; i < lines.length; i++) {
      // Stop if line looks like explanation text (long, natural language)
      if (lines[i].length > 50 && !lines[i].includes(separator === '|' ? '|' : '\t')) {
          break;
      }
      const row = parseRow(lines[i], separator);
      if (row.length === headers.length || (row.length >= headers.length - 1)) {
          rows.push(row);
      }
  }

  if (rows.length === 0) return null;

  // Reconstruct explanation (rest of text)
  const endIndex = dataStartIndex + rows.length;
  // Note: This is a simplified extraction, mostly we return the table structure to be rendered
  const explanation = lines.slice(endIndex).join('\n');

  let html = `<div class="overflow-x-auto my-4 border border-border rounded-lg"><table class="w-full text-sm text-left">`;
  html += `<thead class="bg-primary text-xs uppercase font-semibold text-accent"><tr>`;
  headers.forEach(h => html += `<th class="px-4 py-3 border-b border-border">${h}</th>`);
  html += `</tr></thead><tbody>`;
  
  rows.forEach((row, idx) => {
      html += `<tr class="border-b border-border last:border-0 hover:bg-primary/50 transition-colors">`;
      headers.forEach((_, i) => html += `<td class="px-4 py-2">${row[i] || ''}</td>`);
      html += `</tr>`;
  });
  html += `</tbody></table></div>`;

  return { tableHtml: html, explanation };
};

export const sanitizeAndFormat = (text: string) => {
    // Basic sanitization escape
    const escapeHtml = (unsafe: string) => {
        return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
     };
    
     // If it's a code block, leave it for markdown parser
     if (text.trim().startsWith('```')) return text;

     const tableData = extractTableFromText(text);
     if (tableData) {
         return tableData.tableHtml + (tableData.explanation ? `\n\n${tableData.explanation}` : '');
     }

     return text;
};
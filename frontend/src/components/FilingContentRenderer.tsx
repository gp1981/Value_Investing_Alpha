import React from 'react';

interface FilingContentRendererProps {
  content: string;
  searchQuery?: string;
}

function highlightText(text: string, query?: string): React.ReactNode {
  if (!query || !query.trim()) return text;
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`(${escaped})`, 'gi');
  const parts = text.split(regex);
  return parts.map((part, idx) =>
    part.toLowerCase() === query.toLowerCase() ? (
      <mark key={idx} className="bg-yellow-500/40 text-yellow-200 px-0.5 rounded font-bold">
        {part}
      </mark>
    ) : (
      part
    )
  );
}

/**
 * Renders SEC filing text & Markdown tables in a clean Bloomberg-terminal monospace layout.
 * Converts pipe-delimited Markdown tables (from edgartools) into structured HTML tables.
 */
export const FilingContentRenderer: React.FC<FilingContentRendererProps> = ({ content, searchQuery }) => {
  const lines = content.split('\n');
  const blocks: Array<{ type: 'table'; rows: string[][] } | { type: 'heading'; level: number; text: string } | { type: 'text'; lines: string[] }> = [];

  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // Detect Markdown table block: line starts and ends with | or has multiple |
    if (trimmed.startsWith('|') && trimmed.includes('|', 1)) {
      const tableRows: string[][] = [];
      while (i < lines.length) {
        const tLine = lines[i].trim();
        if (!tLine.startsWith('|')) break;
        // Skip separator rows like | --- | ---: |
        const isSeparator = /^\|[\s:-]+\|$/.test(tLine.replace(/\|/g, '|').replace(/[^|\s:-]/g, 'x')) && /^[|\s:-]+$/.test(tLine);
        if (!isSeparator) {
          const cells = tLine
            .replace(/^\|/, '')
            .replace(/\|$/, '')
            .split('|')
            .map((c) => c.trim());
          tableRows.push(cells);
        }
        i++;
      }
      if (tableRows.length > 0) {
        blocks.push({ type: 'table', rows: tableRows });
      }
      continue;
    }

    // Detect Markdown headings (#, ##, ###)
    const headingMatch = /^(#{1,4})\s+(.*)$/.exec(trimmed);
    if (headingMatch) {
      blocks.push({ type: 'heading', level: headingMatch[1].length, text: headingMatch[2] });
      i++;
      continue;
    }

    // Regular text lines
    const textLines: string[] = [];
    while (i < lines.length) {
      const cur = lines[i].trim();
      if ((cur.startsWith('|') && cur.includes('|', 1)) || /^(#{1,4})\s+/.test(cur)) {
        break;
      }
      textLines.push(lines[i]);
      i++;
    }
    blocks.push({ type: 'text', lines: textLines });
  }

  return (
    <div className="space-y-2.5 text-[11.5px] leading-relaxed font-mono text-terminal-text select-text">
      {blocks.map((block, bIdx) => {
        if (block.type === 'heading') {
          return (
            <div
              key={bIdx}
              className={`font-bold border-b border-terminal-border/50 pb-1 pt-2 ${
                block.level === 1
                  ? 'text-sm text-terminal-green'
                  : block.level === 2
                  ? 'text-xs text-terminal-cyan'
                  : 'text-xs text-amber-300'
              }`}
            >
              {highlightText(block.text, searchQuery)}
            </div>
          );
        }

        if (block.type === 'table') {
          const [headerRow, ...bodyRows] = block.rows;
          return (
            <div key={bIdx} className="overflow-x-auto my-2 border border-terminal-border rounded bg-terminal-panel">
              <table className="w-full text-[11px] tabular-numbers border-collapse">
                <thead>
                  <tr className="bg-terminal-card border-b border-terminal-border text-terminal-cyan">
                    {headerRow.map((cell, cIdx) => (
                      <th
                        key={cIdx}
                        className={`py-1 px-2.5 font-bold whitespace-nowrap ${
                          cIdx === 0 ? 'text-left' : 'text-right'
                        }`}
                      >
                        {highlightText(cell, searchQuery)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-terminal-border/30">
                  {bodyRows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-terminal-bg/60">
                      {row.map((cell, cIdx) => {
                        const isNumeric = /^[\$\(\)\-\d,\.%]+$/.test(cell.trim());
                        return (
                          <td
                            key={cIdx}
                            className={`py-1 px-2.5 ${
                              cIdx === 0 && !isNumeric ? 'text-left text-terminal-text' : 'text-right text-terminal-muted whitespace-nowrap'
                            }`}
                          >
                            {highlightText(cell, searchQuery)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }

        return (
          <div key={bIdx} className="whitespace-pre-wrap">
            {highlightText(block.lines.join('\n'), searchQuery)}
          </div>
        );
      })}
    </div>
  );
};

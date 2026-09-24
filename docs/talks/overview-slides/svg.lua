-- Preserve Quarto's prerendered SVG verbatim: Pandoc otherwise parses some
-- sequence-diagram CSS as Markdown. keep-md saves this input before filters run.
local diagrams = {}
local source = quarto.doc.input_file:gsub('%.qmd$', '.revealjs.md')
local file = assert(io.open(source, 'r'), 'Missing Quarto SVG intermediate: ' .. source)
local markdown = file:read('*a')
file:close()
for svg in markdown:gmatch('(<svg%s.-</svg>)') do
  assert(not svg:match('<foreignObject'), 'Mermaid must use SVG text labels')
  -- Quarto's default 960 x 480 size must not override the diagram's viewBox.
  svg = svg:gsub('^(<svg.-)>', function(tag)
    return tag:gsub('%swidth="[^"]*"', ''):gsub('%sheight="[^"]*"', '') .. '>'
  end)
  -- An SVG image isolates Mermaid typography from Reveal and PDF styles.
  -- Quarto serializes SVG through HTML, lowercasing case-sensitive XML attributes.
  for lower, canonical in pairs({viewbox='viewBox', markerwidth='markerWidth',
      markerheight='markerHeight', refx='refX', refy='refY',
      preserveaspectratio='preserveAspectRatio', textlength='textLength',
      lengthadjust='lengthAdjust'}) do
    svg = svg:gsub(' ' .. lower .. '=', ' ' .. canonical .. '=')
  end
  svg = svg:gsub(' xlink=', ' xmlns:xlink=')
  svg = svg:gsub('^(<svg)', '%1 font-family="Arial, Helvetica, sans-serif"')
  table.insert(diagrams, svg)
end
local index = 0
return {{
  Div = function(el)
    if el.classes:includes('cell-output-display') then
      local html = pandoc.write(pandoc.Pandoc(el.content), 'html')
      if html:match('<svg') then
        index = index + 1
        local svg = assert(diagrams[index], 'Missing static Mermaid SVG')
        local encoded = pandoc.pipe('python', {'-c',
          "import base64,sys; sys.stdout.write(base64.b64encode(sys.stdin.buffer.read()).decode('ascii'))"}, svg)
        el.content = {pandoc.RawBlock('html', '<img class="mermaid-svg" alt="Mermaid diagram" src="data:image/svg+xml;base64,' .. encoded .. '">')}
        return el
      end
    end
  end,
  Pandoc = function(doc)
    assert(index == #diagrams, 'Static Mermaid SVG count does not match rendered cells')
    return doc
  end
}}

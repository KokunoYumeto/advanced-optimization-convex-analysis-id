-- Keep the page-addressed source block together when the PDF has room.
function Div(element)
  if FORMAT:match("latex") and element.classes:includes("source-page") then
    return {
      pandoc.RawBlock("latex", "\\Needspace{10\\baselineskip}"),
      element,
    }
  end
  return element
end

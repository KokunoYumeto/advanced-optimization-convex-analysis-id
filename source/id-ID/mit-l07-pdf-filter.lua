-- Keep source-addressed blocks with their opening content when space permits.
function Div(element)
  if FORMAT:match("latex") and element.classes:includes("source-page") then
    return {
      pandoc.RawBlock("latex", "\\Needspace{9\\baselineskip}"),
      element,
    }
  end
  return element
end

-- Keep source-addressed blocks with their opening content when space permits.
function Div(element)
  if FORMAT:match("latex") then
    if element.classes:includes("source-page") then
      return {
        pandoc.RawBlock("latex", "\\Needspace{9\\baselineskip}"),
        element,
      }
    end
    if element.classes:includes("keep-display-intro") then
      return {
        pandoc.RawBlock("latex", "\\Needspace{5\\baselineskip}"),
        element,
      }
    end
  end
  return element
end

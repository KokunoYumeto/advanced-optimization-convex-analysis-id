-- Keep source-addressed blocks with their opening content when space permits.
function Div(element)
  if FORMAT:match("latex") then
    if element.classes:includes("source-page") then
      if element.identifier == "d90-mit-l11-p086" then
        return {
          pandoc.RawBlock("latex", "\\clearpage"),
          element,
        }
      end
      return {
        pandoc.RawBlock("latex", "\\Needspace{9\\baselineskip}"),
        element,
      }
    end
    if element.classes:includes("edition-correction") or element.classes:includes("keep-display-intro") then
      return {
        pandoc.RawBlock("latex", "\\Needspace{5\\baselineskip}"),
        element,
      }
    end
    if element.classes:includes("keep-proof-conclusion") then
      return {
        pandoc.RawBlock("latex", "\\Needspace{12\\baselineskip}"),
        element,
      }
    end
  end
  return element
end

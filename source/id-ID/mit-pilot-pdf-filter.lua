-- Keep the final two-subitem source bullet on one PDF page.
function Div(element)
  if FORMAT:match("latex") and element.identifier == "d90-mit-l01-p004-i005" then
    return {
      pandoc.RawBlock("latex", "\\Needspace{8\\baselineskip}"),
      element,
    }
  end
  return element
end

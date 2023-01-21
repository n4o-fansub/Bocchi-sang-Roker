function createAlphaTiming(lineDur) 
    local fadeIn, fadeOut = tenv.orgline.raw:match("\\fad%((%d+),(%d+)%)")
    fadeIn = tonumber(fadeIn or "0")
    fadeOut = tonumber(fadeOut or "0")
    local timingText = "\\1a&HFF&"
    if fadeIn > 0 then
        timingText = timingText .. "\\t(0," .. fadeIn - 45 .. ",\\1a&H00&)"
    end
    if fadeOut > 0 then
        endStart = lineDur - fadeOut
        endEnd = endStart + 45
        timingText = timingText .. "\\t(" .. endStart .. "," .. endEnd .. ",\\1a&HFF&)"
    end
    return timingText
end
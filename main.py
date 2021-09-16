import numpy
import os
import re
from src.PathControlPoint import PathControlPoint
from src.SliderPath import SliderPath
from sympy.functions.elementary.integers import ceiling

def main():
    
    for file in os.listdir("."):
        if file.endswith(".osu"):
            FD = open(file, 'r', encoding="utf8")
            FDW = open(file[:-5]+"-INVIS].osu", 'w', encoding="utf8")
            lines = FD.readlines()
            sliders = []
            
            # Finding global sv multiplier
            gsv = -1
            for line in lines:
                match = re.search(r"SliderMultiplier:(\d+(\.\d+)?)", line)
                if match:
                    gsv = float(match.group(1))
                    if (gsv < 0.4):
                        gsv = 0.4
                    if (gsv > 3.6):
                        gsv = 3.6
            if (gsv == -1):
                FDW.write("SliderMultiplier is NaN or not found in %s" % (file))
                exit()
            
            # Making a list of bpm*sv points
            insideTPts = False
            bpmpts = []
            curbpm = 0
            for line in lines:
                if line == "[TimingPoints]\n":
                    insideTPts = True
                if insideTPts and line == "\n":
                    insideTPts = False
                
                match = re.search(r"^(\d+),(\d+(\.\d+)?(E(\+|-)\d+)?),(\d+),(\d+),(\d+),(\d+),1,", line)
                if match and insideTPts:
                    curbpm = float(60000/float(match.group(2)))
                    bpmpts.append((int(match.group(1)), curbpm))
                
                match = re.search(r"^(\d+),(-?\d+(\.\d+)?(E(\+|-)\d+)?),\d+,\d+,\d+,\d+,0", line)
                if match and insideTPts:
                    bpmpts.append((int(match.group(1)), float(-100*curbpm/float(match.group(2)))))
                    
            # Searching for sliders with no reverses (slides=1)
            for line in lines:
                match = re.search(r"^(-?\d+),(-?\d+),(\d+),(\d+),(\d+),(B|P|L)(\|(-?\d+:-?\d+))*,1,(\d+(\.\d+)?)", line)
                if match:
                    xpos = int(match.group(1))
                    ypos = int(match.group(2))
                    time = int(match.group(3))
                    objtype = int(match.group(4))
                    hitSound = int(match.group(5))
                    sliderType = match.group(6)
                    rest = re.sub(r"^(-?\d+),(-?\d+),(\d+),(\d+),(\d+),(B|P|L)", "", line)
                    positionsstring = rest[0:rest.find(",")]
                    positions = re.findall(r"\|(-?\d+:-?\d+)", positionsstring)                    
                    rest = re.sub(r"^(\|-?\d+:-?\d+)*,", "", rest)
                    match = re.search(r"^(\d+),(\d+(\.\d+)?)", rest)
                    slides = int(match.group(1))
                    length = float(match.group(2))
                    rest = re.sub(r"^(\d+),(\d+(\.\d+)?)", "", rest)
                    
                    poslist = []
                    for entry in positions:
                        match2 = re.search(r"(-?\d+):(-?\d+)", entry)
                        pos = (int(match2.group(1)), int(match2.group(2)))
                        poslist.append(pos)
                    
                    # The value passed to bpm isn't actually just the bpm - it's the bpm times the current sv multiplier, or what the bpm would have to be if the sv multiplier were 1  at that point.
                    # The way I'm getting this is very ugly but it does work
                    sliders.append(processSlider(bpmpts[numpy.where(numpy.array(bpmpts)[:,0] <= time)[0][-1]][1], gsv, xpos, ypos, time, objtype, hitSound, sliderType, poslist, slides, length, rest))
                        
                        
            
            # Making new .osu file
            insideTPts = False
            unchangedline = True
            prevtimingpoint = (-1, -1, -1, -1, -1, -1, -1)
            for line in lines:
                unchangedline = True
                if line == "[TimingPoints]\n":
                    insideTPts = True
                if insideTPts and line == "\n":
                    insideTPts = False
                    
                    unchangedline = False
                    # Collect all sliders that occur after the last processed timing point, and make their timing points
                    matchingsliders = [s for s in sliders if s[9] != 0 and s[2] > prevtimingpoint[0]]
                    rest = re.sub(r"^(\d+),(\d+(\.\d+)?),(\d+),(\d+),(\d+),(\d+),1,", "", line)
                    if matchingsliders:
                        for s in matchingsliders:
                            # We move the slider back one ms so that timing for the rest of the song doesn't get offset by +1ms
                            FDW.write("%d,%.15E,%s,%s,%s,%s,1,%s" % (s[2]-1, s[9], prevtimingpoint[2], prevtimingpoint[3], prevtimingpoint[4], prevtimingpoint[5], prevtimingpoint[6]))
                            FDW.write("%d,NaN,%s,%s,%s,%s,0,%s" % (s[2]-1, prevtimingpoint[2], prevtimingpoint[3], prevtimingpoint[4], prevtimingpoint[5], prevtimingpoint[6]))
                            FDW.write("%d,%.15E,%s,%s,%s,%s,1,%s" % (s[2], 60000/(bpmpts[numpy.where(numpy.array(bpmpts)[:,0] == prevtimingpoint[0])[0][-1]][1]*prevtimingpoint[1]/-100), prevtimingpoint[2], prevtimingpoint[3], prevtimingpoint[4], prevtimingpoint[5], prevtimingpoint[6]))
                            FDW.write("%d,%.15E,%s,%s,%s,%s,0,%s" % (s[2], prevtimingpoint[1], prevtimingpoint[2], prevtimingpoint[3], prevtimingpoint[4], prevtimingpoint[5], prevtimingpoint[6]))
                    FDW.write("\n")
                
                # Uninherited timing point matching
                match = re.search(r"^(\d+),(\d+(\.\d+)?(E(\+|-)\d+)?),(\d+),(\d+),(\d+),(\d+),1,", line)
                if match and insideTPts:
                    unchangedline = False
                    # Collect all sliders that occur before the currently processing timing point and after the previously processed timing point, and make their timing points
                    matchingsliders = [s for s in sliders if (s[9] != 0 and (s[2] > prevtimingpoint[0] and s[2] < int(match.group(1))))]
                    rest = re.sub(r"^(\d+),(\d+(\.\d+)?(E(\+|-)\d+)?),(\d+),(\d+),(\d+),(\d+),1,", "", line)
                    if matchingsliders:
                        for s in matchingsliders:
                            # We move the slider back one ms so that timing for the rest of the song doesn't get offset by +1ms
                            FDW.write("%d,%.15E,%s,%s,%s,%s,1,%s" % (s[2]-1, s[9], prevtimingpoint[2], prevtimingpoint[3], prevtimingpoint[4], prevtimingpoint[5], prevtimingpoint[6]))
                            FDW.write("%d,NaN,%s,%s,%s,%s,0,%s" % (s[2]-1, prevtimingpoint[2], prevtimingpoint[3], prevtimingpoint[4], prevtimingpoint[5], prevtimingpoint[6]))
                            FDW.write("%d,%.15E,%s,%s,%s,%s,1,%s" % (s[2], 60000/(bpmpts[numpy.where(numpy.array(bpmpts)[:,0] == prevtimingpoint[0])[0][-1]][1]*prevtimingpoint[1]/-100), prevtimingpoint[2], prevtimingpoint[3], prevtimingpoint[4], prevtimingpoint[5], prevtimingpoint[6]))
                            FDW.write("%d,%.15E,%s,%s,%s,%s,0,%s" % (s[2], prevtimingpoint[1], prevtimingpoint[2], prevtimingpoint[3], prevtimingpoint[4], prevtimingpoint[5], prevtimingpoint[6]))
                    
                    # Override uninherited timing point if it occurs at the same time as the sliders' timing points
                    matchingsliders = [s for s in sliders if (s[9] != 0 and s[2] == int(match.group(1)))]
                    if matchingsliders:
                        s = matchingsliders[0]
                        # We move the slider back one ms so that timing for the rest of the song doesn't get offset by +1ms
                        FDW.write("%d,%.15E,%s,%s,%s,%s,1,%s" % (s[2]-1, s[9], match.group(6), match.group(7), match.group(8), match.group(9), rest))
                        FDW.write("%d,NaN,%s,%s,%s,%s,0,%s" % (s[2]-1, match.group(6), match.group(7), match.group(8), match.group(9), rest))
                        FDW.write("%d,%s,%s,%s,%s,%s,1,%s" % (s[2], match.group(2), match.group(6), match.group(7), match.group(8), match.group(9), rest))
                    else:
                        FDW.write(line)
                    
                    # prevtimingpoint = (time, inherited timing point beatLength, meter, sampleSet, sampleIndex, volume, effects)
                    # Inherited timing point beatLength is -100 because it is treated as the default (which is -100) until an inherited timing point sets it.
                    prevtimingpoint = (int(match.group(1)), -100, match.group(6), match.group(7), match.group(8), match.group(9), rest)
                
                # Inherited timing point matching
                match = re.search(r"^(\d+),(-?\d+(\.\d+)?(E(\+|-)\d+)?),(\d+),(\d+),(\d+),(\d+),0,", line)
                if match and insideTPts:
                    unchangedline = False
                    # Collect all sliders that occur before the currently processing timing point and after the previously processed timing point, and make their timing points
                    matchingsliders = [s for s in sliders if (s[9] != 0 and (s[2] > prevtimingpoint[0] and s[2] < int(match.group(1))))]
                    rest = re.sub(r"^(\d+),(-?\d+(\.\d+)?(E(\+|-)\d+)?),(\d+),(\d+),(\d+),(\d+),0,", "", line)
                    if matchingsliders:
                        for s in matchingsliders:
                            # We move the slider back one ms so that timing for the rest of the song doesn't get offset by +1ms
                            FDW.write("%d,%.15E,%s,%s,%s,%s,1,%s" % (s[2]-1, s[9], prevtimingpoint[2], prevtimingpoint[3], prevtimingpoint[4], prevtimingpoint[5], prevtimingpoint[6]))
                            FDW.write("%d,NaN,%s,%s,%s,%s,0,%s" % (s[2]-1, prevtimingpoint[2], prevtimingpoint[3], prevtimingpoint[4], prevtimingpoint[5], prevtimingpoint[6]))
                            FDW.write("%d,%.15E,%s,%s,%s,%s,1,%s" % (s[2], 60000/(bpmpts[numpy.where(numpy.array(bpmpts)[:,0] == prevtimingpoint[0])[0][-1]][1]*prevtimingpoint[1]/-100), prevtimingpoint[2], prevtimingpoint[3], prevtimingpoint[4], prevtimingpoint[5], prevtimingpoint[6]))
                            FDW.write("%d,%.15E,%s,%s,%s,%s,0,%s" % (s[2], prevtimingpoint[1], prevtimingpoint[2], prevtimingpoint[3], prevtimingpoint[4], prevtimingpoint[5], prevtimingpoint[6]))
                    
                    # Override inherited timing point if it occurs at the same time as the sliders' timing points
                    matchingsliders = [x for x in sliders if (x[9] != 0 and x[2] == int(match.group(1)))]
                    if matchingsliders:
                        s = matchingsliders[0]
                        # We move the slider back one ms so that timing for the rest of the song doesn't get offset by +1ms
                        FDW.write("%d,%.15E,%s,%s,%s,%s,1,%s" % (s[2]-1, s[9], match.group(6), match.group(7), match.group(8), match.group(9), rest))
                        FDW.write("%d,NaN,%s,%s,%s,%s,0,%s" % (s[2]-1, match.group(6), match.group(7), match.group(8), match.group(9), rest))
                        FDW.write("%d,%.15E,%s,%s,%s,%s,1,%s" % (s[2], 60000/(bpmpts[numpy.where(numpy.array(bpmpts)[:,0] == s[2])[0][-1]][1]*float(match.group(2))/-100), match.group(6), match.group(7), match.group(8), match.group(9), rest))
                        FDW.write("%d,%s,%s,%s,%s,%s,0,%s" % (s[2], match.group(2), match.group(6), match.group(7), match.group(8), match.group(9), rest))
                    else:
                        FDW.write(line)
                    
                    # prevtimingpoint = (time, inherited timing point beatLength, meter, sampleSet, sampleIndex, volume, effects)
                    prevtimingpoint = (int(match.group(1)), float(match.group(2)), match.group(6), match.group(7), match.group(8), match.group(9), rest)
                
                # Slider HitObject matching
                match = re.search(r"^(-?\d+),(-?\d+),(\d+),(\d+),(\d+),(B|P|L)(\|(-?\d+:-?\d+))*,(\d+),(\d+(\.\d+)?)", line)
                if match:
                    unchangedline = False
                    matchingsliders = [x for x in sliders if (x[9] != 0 and x[2] == int(match.group(3)))]
                    if matchingsliders:
                        s = matchingsliders[0]
                        # We move the slider back one ms so that timing for the rest of the song doesn't get offset by +1ms
                        FDW.write("%d,%d,%d,%d,%d,L|%s,%d,%f%s" % (s[0], s[1], s[2]-1, s[3], s[4], "|".join(":".join(str(y) for y in x) for x in s[5]), s[6], s[7], s[8]))
                    else:
                        FDW.write(line)
                        
                match = re.search(r"^Version:(.*)$", line)
                if match:
                    unchangedline = False
                    FDW.write("Version:%s-INVIS\n" % match.group(1))
                    
                if unchangedline:
                    FDW.write(line)
                    
            FDW.close()
            FD.close()
            
def processSlider(bpm, gsv, xpos, ypos, time, objtype, hitSound, sliderType, poslist, slides, length, rest):
    if sliderType == "L":
        pathtype = PathControlPoint.LINEAR
    elif sliderType == "P":
        pathtype = PathControlPoint.PERFECT
    else:
        pathtype = PathControlPoint.BEZIER
        
    # Convert poslist to list of PathControlPoints
    ControlPoints = [PathControlPoint(numpy.array((xpos,ypos), dtype='int64'), pathtype)]
    for i in range(0,len(poslist)):
        if i<len(poslist)-1 and poslist[i] == poslist[i+1]:
            continue
        elif i>0 and poslist[i-1] == poslist[i]:
            # We have a new segment starting here
            ControlPoints.append(PathControlPoint(numpy.array(poslist[i], dtype='int64'), pathtype))
        else:
            ControlPoints.append(PathControlPoint(numpy.array(poslist[i], dtype='int64'), None))
        
    sliderpath = SliderPath(ControlPoints, length)
    
    xpoints = []
    ypoints = []
    tlen = round(1000*length/(5/3*bpm*gsv))
    
    # sliderpath.PositionAt returns the loaction of the sliderball pre-snap. We want post-snap so this requires some additional structure.
    # First we calculate how many ms each linear segment is used for
    mspersegment = [0]*len(sliderpath.cumulativeLength)
    for i in range(0,tlen+1):
        idx = sliderpath.indexOfDistance(sliderpath.progressToDistance(i/tlen))
        if idx < 0:
            idx = 0
        if idx > len(mspersegment):
            idx = len(mspersegment)-1
        mspersegment[idx] += 1
    # Edge case handled separately; if the index of the progress to distance is 0 then we consider it to simply be the first point.
    for j in range(0,mspersegment[0]):
        pt = sliderpath.calculatedPath[0]
        xpoints.append(round(pt[0]))
        ypoints.append(round(pt[1]))
    for i in range(1,len(mspersegment)):
        p0 = sliderpath.calculatedPath[i-1]
        p1 = sliderpath.calculatedPath[i]
        for j in range(1,mspersegment[i]+1):
            pt = p0+(p1-p0)*j/mspersegment[i]
            xpoints.append(round(pt[0]))
            ypoints.append(round(pt[1]))
    
    # Define newposlist
    newposlist = []
    framedist = 2*67141632+2*33587200+xpos+ypos-xpoints[0]-ypoints[0]
    snaptol = 50000;
    
    newposlist.append((4196352+xpos, ypos))
    newposlist.append((4196352+xpos, 2099200+ypos))
    newposlist.append((8392704+xpos, 2099200+ypos))
    newposlist.append((8392704+xpos, 4198400+ypos))
    newposlist.append((16785408+xpos, 4198400+ypos))
    newposlist.append((16785408+xpos, 8396800+ypos))
    newposlist.append((33570816+xpos, 8396800+ypos))
    newposlist.append((33570816+xpos, 16793600+ypos))
    newposlist.append((67141632+xpos, 16793600+ypos))
    newposlist.append((67141632+xpos, 33587200+ypos+snaptol))
    newposlist.append((67141632+xpos, ypoints[0]))
    newposlist.append((xpoints[0], ypoints[0]))
    curlen = framedist+2*snaptol;
    for t in range(1,tlen):
        newposlist.append((67141632+xpos, ypoints[t-1]))
        newposlist.append((67141632+xpos, round(33587200+0.5*(ypos-xpos+xpoints[t-1]+xpoints[t]+ypoints[t-1]+ypoints[t]-xpoints[0]-ypoints[0]))))
        if ((ypos-xpos+xpoints[t-1]+xpoints[t]+ypoints[t-1]+ypoints[t]-xpoints[0]-ypoints[0]) % 2 == 1):
            curlen = curlen+1
        
        # This adds and subtracts a bunch of things to cancel everything
        # out (sometimes the rounding will add an extra pixel) and make
        # sure the length the slider travels to get to each pixel we want
        # the sliderball to appear on stays the same.
        
        newposlist.append((67141632+xpos, ypoints[t]))
        newposlist.append((xpoints[t], ypoints[t]))
        curlen = curlen + framedist
    
    # Fixes some rendering issues by making the last segment of length 0
    newposlist.append(newposlist[-1])
    newposlist.append(newposlist[-1])
        
    return (xpos, ypos, time, objtype, hitSound, newposlist, slides, curlen, rest, 5/3*gsv*60/framedist)

if __name__=="__main__": main()
import numpy

# <summary>
# Creates a piecewise-linear approximation of a bezier curve, by adaptively repeatedly subdividing
# the control points until their approximation error vanishes below a given threshold.
# </summary>
# <param name="controlPoints">The control points as a list of numpy arrays (vectors).</param>
# <returns>A list of vectors representing the piecewise-linear approximation.</returns>

def ApproximateBezier(controlPoints):
    return ApproximateBSpline(controlPoints)

# <summary>
# Creates a piecewise-linear approximation of a clamped uniform B-spline with polynomial order p,
# by dividing it into a series of bezier control points at its knots, then adaptively repeatedly
# subdividing those until their approximation error vanishes below a given threshold.
# Retains previous bezier approximation functionality when p is 0 or too large to create knots.
# Algorithm unsuitable for large values of p with many knots.
# </summary>
# <param name="controlPoints">The control points as a list of numpy arrays (vectors).</param>
# <param name="p">The polynomial order.</param>
# <returns>A list of vectors representing the piecewise-linear approximation.</returns>

def ApproximateBSpline(controlPoints):
    p=0
    output = []
    n = len(controlPoints)-1
    
    if (n<0):
        return output
    
    toFlatten = []
    freeBuffers = []
    points = []
    for i in range(0, len(controlPoints)):
        points.append(controlPoints[i])
    
    if (p>0 and p<n):
        # Subdivide B-spline into bezier control points at knots
        for i in range(0, n-p):
            subBezier = [0]*(p+1)
            subBezier[0] = points[i]
            
            # Destructively insert the knot p-1 times via Boehm's algorithm.
            for j in range(0, p-1):
                subBezier[j+1] = points[i+1]
                
                for k in range(1,p-j):
                    l = min((k,n-p-i))
                    points[i+k] = (l*points[i+k]+points[i+k+1])/(l+1)
                
            subBezier[p] = points[i+1]
            toFlatten.append(subBezier)
        
        toFlatten.append(points[(n-p):])
        # Reverse the stack so elements can be accessed in order.
        toFlatten = toFlatten.reverse()
    else:
        # B-spline subdivision unnecessary, degenerate to single bezier.
        p = n
        toFlatten.append(points)
        
    # "toFlatten" contains all the curves which are not yet approximated well enough.
    # We use a stack to emulate recursion without the risk of running into a stack overflow.
    # (More specifically, we iteratively and adaptively refine our curve with a
    # <a href="https://en.wikipedia.org/wiki/Depth-first_search">Depth-first search</a>
    # over the tree resulting from the subdivisions we make.)
        
    subdivisionBuffer1 = [0]*(p+1)
    subdivisionBuffer2 = [0]*(p*2+1)
    leftChild = subdivisionBuffer2
    
    while (len(toFlatten) > 0):
        parent = toFlatten.pop()
        if (bezierIsFlatEnough(parent)):
            # If the control points we currently operate on are sufficiently "flat", we use
            # an extension to De Casteljau's algorithm to obtain a piecewise-linear approximation
            # of the bezier curve represented by our control points, consisting of the same amount
            # of points as there are control points
            bezierApproximate(parent, output, subdivisionBuffer1, subdivisionBuffer2, p+1)
            
            freeBuffers.append(parent)
            continue
        
        # If we do not yet have a sufficiently "flat" (in other words, detailed) approximation we keep
        # subdividing the curve we are currently operating on.
        rightChild = freeBuffers.pop() if len(freeBuffers) > 0 else [0]*(p+1)
        bezierSubdivide(parent, leftChild, rightChild, subdivisionBuffer1, p+1)
        
        # We re-use the buffer of the parent for one of the children, so that we save one allocation per iteration.
        for i in range(0, p+1):
            parent[i] = leftChild[i]
        
        toFlatten.append(rightChild)
        toFlatten.append(parent)
        
    output.append(controlPoints[n])
    return output

# <summary>
# Creates a piecewise-linear approximation of a circular arc curve.
# </summary>
# <param name="controlPoints">The control points as a list of numpy arrays (vectors).</param>
# <returns>A list of vectors representing the piecewise-linear approximation.</returns>

def ApproximateCircularArc(controlPoints):
    circular_arc_tolerance = 0.1
    
    a = controlPoints[0]
    b = controlPoints[1]
    c = controlPoints[2]
    
    aSq = numpy.dot(b-c,b-c)
    bSq = numpy.dot(a-c,a-c)
    cSq = numpy.dot(a-b,a-b)
    
    # If we have a degenerate triangle where a side-length is almost zero, then give up and fall
    # back to a more numerically stable method.
    if (numpy.isclose(aSq, 0) or numpy.isclose(bSq, 0) or numpy.isclose(cSq, 0)):
        return []
    
    s = aSq*(bSq+cSq-aSq)
    t = bSq*(aSq+cSq-bSq)
    u = cSq*(aSq+bSq-cSq)
    
    sumvar = s+t+u
    
    # If we have a degenerate triangle with an almost-zero size, then give up and fall
    # back to a more numerically stable method.
    if (numpy.isclose(sumvar, 0)):
        return []

    centre = (s*a+t*b+u*c)/sumvar
    dA = a-centre
    dC = c-centre
    
    r = numpy.linalg.norm(dA)
    
    thetaStart = numpy.arctan2(dA[1], dA[0])
    thetaEnd = numpy.arctan2(dC[1], dC[0])
    while (thetaEnd < thetaStart):
        thetaEnd = thetaEnd + 2*numpy.pi
        
    dirvar = 1
    thetaRange = thetaEnd-thetaStart
    
    # Decide in which direction to draw the circle, depending on which side of
    # AC B lies.
    orthoAtoC = c-a
    orthoAtoC = numpy.array([orthoAtoC[1], -1*orthoAtoC[0]])
    
    if (numpy.dot(orthoAtoC, b-a) < 0):
        dirvar = -1*dirvar
        thetaRange = 2*numpy.pi-thetaRange
        
    # We select the amount of points for the approximation by requiring the discrete curvature
    # to be smaller than the provided tolerance. The exact angle required to meet the tolerance
    # is: 2 * Math.Acos(1 - TOLERANCE / r)
    # The special case is required for extremely short sliders where the radius is smaller than
    # the tolerance. This is a pathological rather than a realistic case.
    amountPoints = 2 if 2*r <= circular_arc_tolerance else max((2, numpy.ceil(thetaRange/(2*numpy.arccos(1-circular_arc_tolerance/r))).astype(numpy.int64)))
    
    output = []
    for i in range(0, amountPoints):
        fract = i/(amountPoints-1)
        theta = thetaStart + dirvar*fract*thetaRange
        o = numpy.array((numpy.cos(theta), numpy.sin(theta)))*r
        output.append(centre+o)
        
    return output

# <summary>
# Creates a piecewise-linear approximation of a linear curve.
# Basically, returns the input.
# </summary>
# <param name="controlPoints">The control points as a list of numpy arrays (vectors).</param>
# <returns>A list of vectors representing the piecewise-linear approximation.</returns>

def ApproximateLinear(controlPoints):
    result = []
    
    for c in controlPoints:
        result.append(c)
        
    return result

# <summary>
# Make sure the 2nd order derivative (approximated using finite elements) is within tolerable bounds.
# NOTE: The 2nd order derivative of a 2d curve represents its curvature, so intuitively this function
#       checks (as the name suggests) whether our approximation is _locally_ "flat". More curvy parts
#       need to have a denser approximation to be more "flat".
# </summary>
# <param name="controlPoints">The control points as a list of numpy arrays (vectors).</param>
# <returns>Whether the control points are flat enough.</returns>

def bezierIsFlatEnough(controlPoints):
    bezier_tolerance=0.25
    
    for i in range(1, len(controlPoints)-1):
        testvec = controlPoints[i-1]-2*controlPoints[i]+controlPoints[i+1]
        if (numpy.dot(testvec,testvec) > bezier_tolerance*bezier_tolerance*4):
            return False
        
    return True

# <summary>
# Subdivides n control points representing a bezier curve into 2 sets of n control points, each
# describing a bezier curve equivalent to a half of the original curve. Effectively this splits
# the original curve into 2 curves which result in the original curve when pieced back together.
# </summary>
# <param name="controlPoints">The control points as a list of numpy arrays (vectors).</param>
# <param name="l">Output: The control points corresponding to the left half of the curve.</param>
# <param name="r">Output: The control points corresponding to the right half of the curve.</param>
# <param name="subdivisionBuffer">The first buffer containing the current subdivision state.</param>
# <param name="count">The number of control points in the original list.</param>

def bezierSubdivide(controlPoints, l, r, subdivisionBuffer, count):
    midpoints = subdivisionBuffer
    
    for i in range(0, count):
        midpoints[i] = controlPoints[i]
        
    for i in range(0, count):
        l[i] = midpoints[0]
        r[count-i-1] = midpoints[count-i-1]
        
        for j in range(0, count-i-1):
            midpoints[j] = (midpoints[j]+midpoints[j+1])/2
            
# <summary>
# This uses <a href="https://en.wikipedia.org/wiki/De_Casteljau%27s_algorithm">De Casteljau's algorithm</a> to obtain an optimal
# piecewise-linear approximation of the bezier curve with the same amount of points as there are control points.
# </summary>
# <param name="controlPoints">The control points as a list of numpy arrays (vectors).</param>
# <param name="output">The points representing the resulting piecewise-linear approximation.</param>
# <param name="count">The number of control points in the original list.</param>
# <param name="subdivisionBuffer1">The first buffer containing the current subdivision state.</param>
# <param name="subdivisionBuffer2">The second buffer containing the current subdivision state.</param>

def bezierApproximate(controlPoints, output, subdivisionBuffer1, subdivisionBuffer2, count):
    l = subdivisionBuffer2
    r = subdivisionBuffer1
    
    bezierSubdivide(controlPoints, l, r, subdivisionBuffer1, count)
    
    for i in range(0, count-1):
        l[count+i] = r[i+1]
        
    output.append(controlPoints[0])
    
    for i in range(1, count-1):
        index = 2*i
        p = 0.25*(l[index-1]+2*l[index]+l[index+1])
        output.append(p)
    

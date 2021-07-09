import numpy

class PathControlPoint:
    
    LINEAR = 0
    PERFECT = 1
    BEZIER = 2
    
    
    Position = numpy.array((0,0), dtype='int64')
    
    Type = None
    
    def __init__(self, position, typevar=None):
        self.Position = position
        self.Type = typevar
        
    def Equals(self, other):
        return (self.Position == other.Position and self.Type == other.Type)
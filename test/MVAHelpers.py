from ROOT import TGraph, TH1F, TFile, TTree, EColor, TLegend
import random
import bisect
import glob

"""
        MVAHelpers.py
        Author: Evan K. Friis, UC Davis (friis@physics.ucdavis.edu)

        Helper functions used in various TauTagTools::MVA training scripts
"""

class TancSet:
   """ Container class of TancCuts - contains a set of cuts corresponding to a TaNC operating point"""
   #Static member pointing to the decay mode info
   DecayModeList = []
   def __init__(self, myCuts):
      self.TancCuts            = myCuts
      self.EstimatedEfficiency = 0
      self.EstimatedFakeRate   = 0
      self.GetEfficiency(myCuts)
   def GetEfficiency(self, cuts):
      if len(cuts) != len(self.DecayModeList):
         raise TancSetException, "Length of cuts not the same as length of decay mode!"
      else:
         self.EstimatedEfficiency = (TancDecayMode.TotalSignalPrepass + sum([ x.SignalPassing(y) for x, y in zip(self.DecayModeList, cuts)]))*1.0/TancDecayMode.TotalSignalEntries
         self.EstimatedFakeRate   = (TancDecayMode.TotalBackgroundPrepass + sum([ x.BackgroundPassing(y) for x, y in zip(self.DecayModeList, cuts)]))*1.0/TancDecayMode.TotalBackgroundEntries
   def GetVeelkenNormalization(self):
      outputList = [ dm.GetSignalFraction() / ( dm.GetSignalFraction() + ( 1/(dm.RescaleCut(daCut)) - 1)*dm.GetBackgroundFraction() ) for dm, daCut in zip(self.DecayModeList, self.TancCuts) ]
      return outputList
   def GetRescaledCuts(self):
      return [ dm.RescaleCut(theCut) for dm, theCut in zip(self.DecayModeList, self.TancCuts) ]
   def __cmp__(self, other):
      # predicate, order by fake rate
      return cmp(self.EstimatedFakeRate, other.EstimatedFakeRate)

class TancDecayMode:
   """ Holds numberOfSignal and nBackground for each decay mode.  Contains the MVA output distributions for both signal and background """
   # Static members
   TotalSignalEntries     = 0
   TotalBackgroundEntries = 0
   TotalSignalPrepass     = 0
   TotalBackgroundPrepass = 0
   def __init__(self, Name, DecayModes, SignalMVAOut, BackgroundMVAOut):
      self.Name              = Name
      self.DecayModes        = DecayModes
      self.NSignal           = SignalMVAOut.GetEntries()
      self.NBackground       = BackgroundMVAOut.GetEntries()
      self.SignalMVAOut      = SignalMVAOut
      self.BackgroundMVAOut  = BackgroundMVAOut
      self.SignalEffCurve    = MakeEfficiencyCurveFromHistogram(SignalMVAOut)
      self.BackgroundEffCurve = MakeEfficiencyCurveFromHistogram(BackgroundMVAOut)
      self.MinMaxTuple       = MergeMinMaxTuples([GetMinimumAndMaximumOccupiedBin(SignalMVAOut), GetMinimumAndMaximumOccupiedBin(BackgroundMVAOut)])
      self.SignalMVAOut.SetTitle("Signal NN output distribution for %s" % self.Name)
      self.BackgroundMVAOut.SetTitle("Background NN output distribution for %s" % self.Name)
      self.SignalMVAOut.GetXaxis().SetTitle("NN output")
      self.BackgroundMVAOut.GetXaxis().SetTitle("NN output")
      self.SignalMVAOut.SetLineColor(EColor.kRed)
      self.BackgroundMVAOut.SetLineColor(EColor.kBlue)
      self.CurveLegend = TLegend(0.7, 0.15, 0.92, 0.4)
      self.CurveLegend.AddEntry(self.SignalMVAOut, "Signal", "l")
      self.CurveLegend.AddEntry(self.BackgroundMVAOut, "Background", "l")
   def SignalAndBackgroundPassing(self, cut):
      return (SignalPassing(self, cut), BackgroundPassing(self,cut))
   def SignalPassing(self, cut):
      return self.NSignal*1.0*self.SignalEffCurve.Eval(cut)
   def BackgroundPassing(self, cut):
      return self.NBackground*1.0*self.BackgroundEffCurve.Eval(cut)
   def GetSignalFraction(self):
      return self.NSignal*1.0/self.TotalSignalEntries
   def GetBackgroundFraction(self):
      return self.NBackground*1.0/self.TotalBackgroundEntries
   def GetDecayModeCutString(self):
      return BuildCutString(self.DecayModes)
   def RescaleCut(self, cut):
      """ Get the cut, rescaled to between 0 and 1 """
      TrueMin, TrueMax = self.MinMaxTuple
      cut -= TrueMin  #scale lower end to zero
      cut /= (TrueMax - TrueMin)
      return cut
   def __str__(self):
      print self.DecayModes
      return ""
      #return CommafyListOfStrings([ PrettifyDecayMode[mode] for mode in self.DecayModes ])


def FakeRateLine(minEff, minFakeRate, maxEff, maxFakeRate):
   """ Returns a lambda function describing a straight line between two eff/fakerate points """
   return lambda eff:( (maxFakeRate - minFakeRate)/(maxEff - minEff) )*(eff - minEff)

class TancOperatingCurve:
   """ Container class of TancSets - maps out a signal/background curve """
   def __init__(self):
      self.TancSets = []
      self.MinimumFakeRate = 1.
      self.EffAtMinimumFakeRate = 1.
      self.MaximumFakeRate = 0.
      self.EffAtMaximumFakeRate = 0.
      self.ApproxFunction = 0

   def InsertOperatingPoint(self, theTancSet):
      """ Insert a new operating point into the curve.  The TancOperatingCurve will manage the points to ensure that the operating point is convex """
      EstimatedFakeRateForThisPoint = theTancSet.EstimatedFakeRate
      EstimatedEffForThisPoint      = theTancSet.EstimatedEfficiency
      #print "Adding %f eff - %f FR" % (EstimatedEffForThisPoint, EstimatedFakeRateForThisPoint)

      # Approximation to reduce array lookups
      # if are away from the endpoints of the curve, compute a straight line from (minFake, minEff) to (maxFake, maxEff)
      # the new point must be below (lower fake rate) than the corresponding point on this line, for the same efficiency.
      if EstimatedEffForThisPoint < self.EffAtMaximumFakeRate and EstimatedFakeRateForThisPoint > self.MinimumFakeRate and EstimatedEffForThisPoint > self.EffAtMinimumFakeRate and EstimatedFakeRateForThisPoint < self.MaximumFakeRate:
         if EstimatedFakeRateForThisPoint > self.ApproxFunction(EstimatedEffForThisPoint):
            return 0

      # Find the point in the curve (ordered by increasing FR) to insert this point
      insertionIndex = bisect.bisect_left(self.TancSets, theTancSet)
      # Check to make sure that our efficiency beats the next lowest fake rate,
      # otherwise we don't really care about this point
      if insertionIndex == 0:
         # if this is the lowest FR yet, always insert
         self.TancSets.insert(0, theTancSet)
         return 0
      # Otherwise check to see if this is a good point - namely,
      # is the signal efficiency higher than the efficiency of the next lower fake rate point?
      # This assures convexity wrt to the next lowest point.  Otherwise, this point sucks and we can 
      # throw it away.
      if self.TancSets[insertionIndex-1].EstimatedEfficiency > EstimatedEffForThisPoint:
         # this point sucks, do nothing
         return 0
      # If we reach this point, the point is a good one.  Now, before insertion, 
      # delete any points that have a higher fake rate, but lower efficiency
      DoneDeleting = False
      EndDeletionIndex = insertionIndex
      while not DoneDeleting and EndDeletionIndex < len(self.TancSets):
         if self.TancSets[EndDeletionIndex].EstimatedEfficiency < EstimatedEffForThisPoint:
            #this point has higher fake rate, but lower eff.  Let's delete it
            EndDeletionIndex += 1
         else:
            # we have guaranteed convexity about the point we are inserting, break
            DoneDeleting = True
      # delete the bad points - we do this first, to preserve the deletion indexes we jut computed
      del self.TancSets[insertionIndex:EndDeletionIndex]
      #Insert our new point
      self.TancSets.insert(insertionIndex, theTancSet)

      # update our approximations
      if EstimatedFakeRateForThisPoint < self.MinimumFakeRate:
         self.MinimumFakeRate = EstimatedFakeRateForThisPoint
         self.EffAtMinimumFakeRate = EstimatedEffForThisPoint
         self.ApproxFunction = FakeRateLine(self.EffAtMinimumFakeRate, self.MinimumFakeRate, self.EffAtMaximumFakeRate, self.MaximumFakeRate)
      elif EstimatedFakeRateForThisPoint > self.MaximumFakeRate:
         self.MaximumFakeRate = EstimatedFakeRateForThisPoint
         self.EffAtMaximumFakeRate = EstimatedEffForThisPoint
         self.ApproxFunction = FakeRateLine(self.EffAtMinimumFakeRate, self.MinimumFakeRate, self.EffAtMaximumFakeRate, self.MaximumFakeRate)
      return 1
   def GetOpCurveTGraph(self):
      """ returns a tuple w/ TGraph describing the eff/bkg, bkg, eff pairs """
      #MinFakeRate = self.TancSets[0].EstimatedFakeRate
      #MaxFakeRate = self.TancSets[len(self.TancSets)-1].EstimatedFakeRate
      outputVersusEff      = TGraph( len(self.TancSets ) )
      outputVersusFakeRate = TGraph( len(self.TancSets ) )
      for index, aCutPoint in enumerate(self.TancSets):
         outputVersusEff.SetPoint(index, aCutPoint.EstimatedEfficiency, aCutPoint.EstimatedFakeRate)
         outputVersusFakeRate.SetPoint(index, aCutPoint.EstimatedFakeRate, aCutPoint.EstimatedEfficiency)
      return (outputVersusEff, outputVersusFakeRate)

def MakeIntegralHistogram(InputHistogram):
   """ produces a TGraph f(x0) giving the percentage of total entries with x > x0 """
   output = TGraph(InputHistogram.GetNbinsX())
   totalEntries = InputHistogram.GetEntries()
   passedSoFar = InputHistogram.GetBinContent(0) #underflow bin
   for x in range(1, InputHistogram.GetNbinsX()+1):
      passedSoFar += InputHistogram.GetBinContent(x)
      output.SetPoint(x, InputHistogram.GetBinCenter(x), passedSoFar*1.0/totalEntries)
   return output

def MakeEffHistogram(numerator, denominator):
   for bin in range(1, denominator.GetNbinsX()+1):
      numeratorContents = numerator.GetBinContent(bin)
      denominatorContents = denominator.GetBinContent(bin)
      if denominatorContents > 0:
         scaled = numeratorContents*1.0/denominatorContents
         numerator.SetBinContent(bin, scaled)


def BuildCutString(decayModeList):
   output = "!__PREFAIL__ && !__ISNULL__ && ("
   for index, aDecayMode in enumerate(decayModeList):
      if aDecayMode == 0:
         output += "(!__PREPASS__ && DecayMode == 0)"  #exclude isolated one prong taus from training, as there is no info
      else:
         output += "DecayMode == %i" % aDecayMode
      if index != len(decayModeList)-1:
         output += " || "
   output += ")"
   return output

def ComputeSeparation(SignalHistogram, BackgroundHistogram):
   ''' Computes statistical seperation between two histograms.  Output will be zero for identically shaped distributions
   and one for distributions with no overlap.'''
   output = 0.0
   nPoints = SignalHistogram.GetNBinsX()
   if nPoints != BackgroundHistogram.GetNBinsX():
      print "Signal and background histograms don't have the same number of points!"
      sys.exit(1)
   SignalEntries     = SignalHistogram.GetEntries()
   BackgroundEntries = BackgroundHistogram.GetEntries()
   for bin in range(1, nPoints+1):
      normalizedSignal = SignalHistogram.GetBinContent(bin)*1.0/SignalEntries
      normalizedBackground = BackgroundHistogram.GetBinContent(bin)*1.0/BackgroundEntries
      output += (normalizedSignal - normalizedBackground)*(normalizedSignal - normalizedBackground)/(normalizedSignal + normalizedBackground)
   return output/2.0

def BuildSingleEfficiencyCurve(SignalHistogram, SignalTotal, BackgroundHistogram, BackgroundTotal, colorIndex):
   ''' Return a TGraph mapping background efficiency to signal efficiencies of a cut applied on two distributions'''
   nPoints = SignalHistogram.GetNBinsX()
   if nPoints != BackgroundHistogram.GetNBinsX():
      print "Signal and background histograms don't have the same number of points!"
      sys.exit(1)
   output = TGraph(nPoints)
   SignalSum = 0.
   BackgroundSum = 0.
   for bin in range(1, nPoints+1):
      SignalSum     += SignalHistogram.GetBinContent(bin)
      BackgroundSum += BackgroundHistogram.GetBinContent(bin)
      SignalEff     =  (1.0*SignalSum)/SignalTotal
      BackgroundEff =  (1.0*BackgroundSum)/BackgroundTotal
      output.SetPoint(bin-1, SignalEff, BackgroundEff)
   return output

# Binning of all efficiency curves.  nBins must be large to accurately build the eff-fake rate curve
EfficiencyCurveBinning = { 'nBins' : 3000, 'xlow' : -3.0, 'xhigh' : 3.0 }

def GetTTreeDrawString(varexp, histoName, nBins = EfficiencyCurveBinning['nBins'], xlow = EfficiencyCurveBinning['xlow'], xhigh = EfficiencyCurveBinning['xhigh']):
   '''Format a TTree Draw->stored histo string.  ROOT is a mess!'''
   return "%(varexp)s>>%(histoName)s(%(nBins)i, %(xlow)f, %(xhigh)f)" % { 'varexp' : varexp, 'histoName' : histoName, 'nBins' : nBins, 'xlow' : xlow, 'xhigh' : xhigh }

def MakeEfficiencyCurveFromHistogram(histogram):
   '''Returns a graph of f(x), where f is percentage of entries in the histogram above x'''
   output = TGraph(histogram.GetNbinsX())
   normalization = histogram.GetEntries()
   integralSoFar = 0.
   for x in xrange(0, histogram.GetNbinsX()):
      integralSoFar += histogram.GetBinContent(x+1)*1.0/normalization
      output.SetPoint(x, histogram.GetBinCenter(x+1), 1.0-integralSoFar)
   return output

def GetMinimumAndMaximumOccupiedBin(histo):
   """ Returns tuple (minX, maxX) of the minimum and maximum non-zero bins in a histogram"""
   nBins = histo.GetNbinsX()
   maxBin = 1
   minBin = nBins
   for iBin in range(1, nBins+1):
      if histo.GetBinContent(iBin):
         if iBin > maxBin:
            maxBin = iBin
         if iBin < minBin:
            minBin = iBin
   return (histo.GetBinLowEdge(minBin), histo.GetBinLowEdge(maxBin) + histo.GetBinWidth(maxBin))

def MergeMinMaxTuples(tupleList):
   """ Merges a list of (min, max) tuples into (MIN, MAX) so that the result spans all of them"""
   less = lambda x, y: x < y and x or y
   more = lambda x, y: x > y and x or y 
   window = lambda x, y: ( less(x[0], y[0]), more(x[1], y[1]) )
   return reduce(window, tupleList)

def PrettifyDecayMode(mode):
   """ Returns a ROOT style latex string translating a decay mode index into a human readable form """
   modeString = ""
   numTracks = (mode / 5) + 1
   numPiZero = mode % 5
   for iter in range(0, numTracks):
      modeString += "#pi"
      modeString += "^{#pm}"
   for iter in range(0, numPiZero):
      modeString += "#pi^{0}"

def CommafyListOfStrings(strings):
   """ Concatenate a list of strings, seperating them when necessary by a comma """
   funcy = lambda x, y: "%s, %s" % (x,y)
   output = reduce(funcy, strings)
   return output

def ListTrainingStatistics():
   summaryFormatString = "%(netname)-25s %(Signal)12i %(Background)15i %(algoname)-30s"
   headerFormatString = "%(netname)-25s %(Signal)12s %(Background)15s %(algoname)-30s"
   print "--------------------------------------------------------------------------------------"
   print headerFormatString % { 'netname' : "Neural net", 'Signal' : "NSignal", 'Background' : "NBackground", 'algoname' : "Algoname"}
   print "--------------------------------------------------------------------------------------"
   for aTrainDir in glob.glob("TrainDir*"):
      printDict = {}
      trainWords = aTrainDir.split("_")
      # get signal entries
      printDict['netname'] = trainWords[1]
      printDict['algoname'] = trainWords[2]
      tempSignalFile = TFile("%s/signal.root" % aTrainDir, "READ")
      tempSignalTree = tempSignalFile.Get("train")
      printDict['Signal'] = tempSignalTree.GetEntries()

      tempBackgroundFile = TFile("%s/background.root" % aTrainDir, "READ")
      tempBackgroundTree = tempBackgroundFile.Get("train")
      printDict['Background'] = tempBackgroundTree.GetEntries()

      print summaryFormatString % printDict



import FWCore.ParameterSet.Config as cms

'''

Common training defintions

Author: Evan K. Friis (UC Davis)

'''

# Base jets of tau production
jet_collection = cms.InputTag('ak5PFJets')

# Kinematic selections
kinematic_selection = cms.string('pt > 5.0 & abs(eta) < 2.5')

# Lead object jet selection
lead_object_jet_selection = cms.string("getPFConstituent(0).pt() > 5.0")

# Basic kinematic plots
kin_plots = cms.VPSet(
    cms.PSet(
        min = cms.untracked.double(0),
        max = cms.untracked.double(100),
        nbins = cms.untracked.int32(100),
        name = cms.untracked.string("pt"),
        description = cms.untracked.string("Pt"),
        plotquantity = cms.untracked.string("pt()"),
        lazyParsing = cms.untracked.bool(True)
    ),
    cms.PSet(
        min = cms.untracked.double(-2.5),
        max = cms.untracked.double(2.5),
        nbins = cms.untracked.int32(100),
        name = cms.untracked.string("eta"),
        description = cms.untracked.string("Eta"),
        plotquantity = cms.untracked.string("eta()"),
        lazyParsing = cms.untracked.bool(True)
    ),
    cms.PSet(
        min = cms.untracked.double(-3.14),
        max = cms.untracked.double(3.14),
        nbins = cms.untracked.int32(100),
        name = cms.untracked.string("phi"),
        description = cms.untracked.string("Phi"),
        plotquantity = cms.untracked.string("phi()"),
        lazyParsing = cms.untracked.bool(True)
    ),
    cms.PSet(
        min = cms.untracked.double(0.0),
        max = cms.untracked.double(10.0),
        nbins = cms.untracked.int32(100),
        name = cms.untracked.string("mass"),
        description = cms.untracked.string("mass"),
        plotquantity = cms.untracked.string("mass()"),
        lazyParsing = cms.untracked.bool(True)
    ),
)

# Jet plots
jet_histograms = cms.VPSet(
    cms.PSet(
        min = cms.untracked.double(0.0),
        max = cms.untracked.double(20.0),
        nbins = cms.untracked.int32(100),
        name = cms.untracked.string("collimation"),
        description = cms.untracked.string("Pt * Width"),
        plotquantity = cms.untracked.string("pt()*sqrt(etaetaMoment())"),
        lazyParsing = cms.untracked.bool(True)
    ),
    cms.PSet(
        min = cms.untracked.double(0.0),
        max = cms.untracked.double(50.0),
        nbins = cms.untracked.int32(100),
        name = cms.untracked.string("leadobject"),
        description = cms.untracked.string("Pt of lead jet object"),
        plotquantity = cms.untracked.string("getPFConstituent(0).pt()"),
        lazyParsing = cms.untracked.bool(True)
    ),
)
jet_histograms.extend(kin_plots)

tau_histograms = cms.VPSet(
    cms.PSet(
        min = cms.untracked.double(-3.5),
        max = cms.untracked.double(20.5),
        nbins = cms.untracked.int32(24),
        name = cms.untracked.string("decaymode"),
        description = cms.untracked.string("DecayMode"),
        plotquantity = cms.untracked.string("decayMode"),
        lazyParsing = cms.untracked.bool(True)
    )
)

tau_histograms.extend(kin_plots)


tau_histograms.append(
    cms.PSet(
        min = cms.untracked.double(-20.5),
        max = cms.untracked.double(20.5),
        nbins = cms.untracked.int32(41),
        name = cms.untracked.string("decaymodeRes"),
        description = cms.untracked.string("DecayModeRes"),
        plotquantity = cms.untracked.string(
            "decayMode() - bremsRecoveryEOverPLead()"),
        lazyParsing = cms.untracked.bool(True)
    )
)

tau_histograms.append(
    cms.PSet(
        min = cms.untracked.double(-25),
        max = cms.untracked.double(25),
        nbins = cms.untracked.int32(100),
        name = cms.untracked.string("ptRes"),
        description = cms.untracked.string("PtRes"),
        plotquantity = cms.untracked.string("pt()-alternatLorentzVect().pt()"),
        lazyParsing = cms.untracked.bool(True)
    )
)

tau_histograms.append(
    cms.PSet(
        min = cms.untracked.double(-0.5),
        max = cms.untracked.double(-0.5),
        nbins = cms.untracked.int32(100),
        name = cms.untracked.string("etaRes"),
        description = cms.untracked.string("EtaRes"),
        plotquantity = cms.untracked.string("eta()-alternatLorentzVect().eta()"),
        lazyParsing = cms.untracked.bool(True)
    )
)

tau_histograms.append(
    cms.PSet(
        min = cms.untracked.double(-0.5),
        max = cms.untracked.double(0.5),
        nbins = cms.untracked.int32(100),
        name = cms.untracked.string("phiRes"),
        description = cms.untracked.string("phiRes"),
        plotquantity = cms.untracked.string(
            "deltaPhi(phi(), alternatLorentzVect().phi())"),
        lazyParsing = cms.untracked.bool(True)
    )
)

tau_histograms.append(
    cms.PSet(
        min = cms.untracked.double(-5),
        max = cms.untracked.double(5.0),
        nbins = cms.untracked.int32(100),
        name = cms.untracked.string("massRes"),
        description = cms.untracked.string("massRes"),
        plotquantity = cms.untracked.string("mass() - alternatLorentzVect().mass()"),
        lazyParsing = cms.untracked.bool(True)
    )
)
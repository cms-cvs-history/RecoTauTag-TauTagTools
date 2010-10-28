/*
 * RecoTauDecayModeTruthMatchPlugin
 *
 * Author: Evan K. Friis, UC Davis
 *
 * Implements a RecoTauCleaner plugin that returns the difference
 * between the reconstructed decay mode and true decay mode index.
 *
 * By requiring the return value to be zero one can select reco taus
 * that have the decay mode correctly reconstructed.
 *
 * $Id. $
 */

#include "RecoTauTag/RecoTau/interface/RecoTauBuilderPlugins.h"

#include "DataFormats/TauReco/interface/PFTau.h"
#include "DataFormats/TauReco/interface/PFTauFwd.h"
#include "DataFormats/JetReco/interface/GenJet.h"
#include "DataFormats/JetReco/interface/GenJetCollection.h"
#include "DataFormats/Common/interface/Association.h"

#include "PhysicsTools/JetMCUtils/interface/JetMCTag.h"

#include <boost/foreach.hpp>
#include <boost/assign.hpp>
#include <map>

namespace {
  // Convert the string decay mode from PhysicsTools to the
  // PFTau::hadrondicDecayMode format
  static std::map<std::string, reco::PFTau::hadronicDecayMode> dmTranslator =
    boost::assign::map_list_of
    ("oneProng0Pi0", reco::PFTau::kOneProng0PiZero)
    ("oneProng1Pi0", reco::PFTau::kOneProng1PiZero)
    ("oneProng2Pi0", reco::PFTau::kOneProng2PiZero)
    ("oneProngOther", reco::PFTau::kOneProngNPiZero)
    ("threeProng0Pi0", reco::PFTau::kThreeProng0PiZero)
    ("threeProng1Pi0", reco::PFTau::kThreeProng1PiZero)
    ("threeProngOther", reco::PFTau::kThreeProngNPiZero)
    ("electron", reco::PFTau::kNull)
    ("muon", reco::PFTau::kNull);
}

namespace tautools {

class RecoTauDecayModeTruthMatchPlugin : public reco::tau::RecoTauCleanerPlugin
{
  public:
    explicit RecoTauDecayModeTruthMatchPlugin(const edm::ParameterSet& pset);
    virtual ~RecoTauDecayModeTruthMatchPlugin() {}
    double operator()(const reco::PFTauRef&) const;
    void beginEvent();

  private:
    edm::InputTag matchingSrc_;
    typedef edm::Association<reco::GenJetCollection> GenJetAssociation;
    edm::Handle<GenJetAssociation> genTauMatch_;
};

// ctor
RecoTauDecayModeTruthMatchPlugin::RecoTauDecayModeTruthMatchPlugin(
    const edm::ParameterSet& pset): RecoTauCleanerPlugin(pset),
  matchingSrc_(pset.getParameter<edm::InputTag>("matching")) {}

// Called by base class at the beginning of each event
void RecoTauDecayModeTruthMatchPlugin::beginEvent() {
  // Load the matching information
  evt()->getByLabel(matchingSrc_, genTauMatch_);
}

// Determine a number giving the quality of the input tau.  Lower numbers are
// better - zero indicates that the reco decay mode matches the truth.
double RecoTauDecayModeTruthMatchPlugin::operator()(const reco::PFTauRef& tau)
  const {
  GenJetAssociation::reference_type truth = (*genTauMatch_)[tau];
  // Check if the matching exists, if not return +infinity
  if (truth.isNull())
    return std::numeric_limits<double>::infinity();
  // Get the difference in decay mode.  The closer to zero, the more the decay
  // mode is matched.
  return std::abs(
      dmTranslator[JetMCTagUtils::genTauDecayMode(*truth)] - tau->decayMode());
}

} // end tautools namespace

#include "FWCore/Framework/interface/MakerMacros.h"
DEFINE_EDM_PLUGIN(RecoTauCleanerPluginFactory, tautools::RecoTauDecayModeTruthMatchPlugin, "RecoTauDecayModeTruthMatchPlugin");
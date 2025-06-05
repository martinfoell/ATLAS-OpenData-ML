import ROOT
import atlasopenmagic as atom
import ast
import sys
import re


def getSF(dsid):
    xsec = float(atom.get_metadata(dsid, 'cross_section'))
    filter_eff = float(atom.get_metadata(dsid, 'filter_efficiency'))
    k_factor = float(atom.get_metadata(dsid, 'k_factor'))
    sum_weights = float(atom.get_metadata(dsid, 'sum_weights'))

    return (xsec * filter_eff * k_factor) / sum_weights
    
ROOT.EnableImplicitMT()
print(ROOT.GetThreadPoolSize())


atom.available_releases()
atom.set_release('2024r-pp')

df_metadata =  ROOT.RDF.FromCSV("../data/metadata.csv")

print(df_metadata.GetColumnNames())
print(df_metadata.GetColumnType("dataset_number"))
dataset_numbers = df_metadata.Take['Long64_t']("dataset_number").GetValue()
all_metadata = atom.get_metadata('301204')
print(all_metadata)
print(getSF('301204'))

include_keys = set(["lepton", "2electron", "2lepton", "3lepton", "4lepton", "mulitlepton", "ZHiggsw", "ZZ"])
exclude_keys = set(["BSM", "exotic", "2tau"])
exclude_short_name = "ss"


dsid = []
for number in dataset_numbers:
    keywords = set(ast.literal_eval(atom.get_metadata(str(number))['keywords']))
    short_name = atom.get_metadata(str(number))['short_name']
    
    if keywords.intersection(set(["SM", "sm"])) and keywords.intersection(include_keys) and not keywords.intersection(exclude_keys):
        if exclude_short_name not in short_name:
            dsid.append(str(number))

print(dsid)

dsid_urls = []
for number in dsid:
    number_events = atom.get_metadata(str(number))["number_events"]
    dsid_urls.append(atom.get_urls(str(number)))

dsid_urls_flat = [item for sublist in dsid_urls for item in sublist]

dsid_file_numbers = []
for url in dsid_urls_flat:
    match = re.search(r'DAOD_PHYSLITE\.(\d{8})\.', url)
    if match:
        file_number = f".{match.group(1)}."

        if file_number not in dsid_file_numbers:
            dsid_file_numbers.append(file_number)
    else:
        print("No match found")    

names = dsid_file_numbers
weights = [getSF(i) for i in dsid]

weight_expr = ""
for i, (n, w) in enumerate(zip(names, weights)):
    weight_expr += f'rdfsampleinfo_.Contains("{n}") ? {w}f : '

weight_expr += "0.0f"  # if no match

names = dsid_file_numbers
dsid_int = [int(i) for i in dsid]

dsid_expr = ""
for i, (n, w) in enumerate(zip(names, dsid_int)):
    dsid_expr += f'rdfsampleinfo_.Contains("{n}") ? {w} : '

dsid_expr += "0"  # if no match

ROOT.gInterpreter.Declare('''
using VecF_t = const ROOT::RVec<float>&;
using VecD_t = const ROOT::RVec<double>&;
using VecI_t = const ROOT::RVec<int>&;
using VecUI_t = const ROOT::RVec<UInt_t>&;
using VecB_t = const ROOT::VecOps::RVec<bool>;

ROOT::VecOps::RVec<bool> checkIsolation(VecF_t& iso1, VecF_t& iso2, VecF_t& iso3, VecF_t& pt, float cutval){
  ROOT::VecOps::RVec<bool> result;
  for (UInt_t i = 0; i < iso1.size(); i++){
    //if(((TMath::Max(iso1.at(i),iso2.at(i)) + 0.4*iso3.at(i))/pt.at(i)) < cutval){
    result.emplace_back(((TMath::Max(iso1.at(i),iso2.at(i)) + 0.4*iso3.at(i))/pt.at(i)) < cutval);
    //}else{
    //result.push_back(false);
    //} 
  }
  return result;
}


ROOT::RVec<float> getVector(VecF_t& inp1, Float_t m1){
  time_t start = time(NULL);
  ROOT::RVec<float> ret_vec;
  const auto ninp1 = int(inp1.size());
  for (int j=0; j < ninp1; ++j) {
    if(m1)ret_vec.push_back(fabs(inp1.at(j))*m1);
    else ret_vec.push_back(inp1.at(j));
  }
  time_t end = time(NULL);
  return ret_vec;
}


''')

files_to_read = dsid_urls_flat # only read a few files for testing, reomve [0:5] to read all files
# files_to_read = dsid_urls_flat[0:5] # only read a few files for testing, reomve [0:5] to read all files

df_mc = ROOT.RDataFrame("CollectionTree", files_to_read)

ROOT.RDF.Experimental.AddProgressBar(df_mc)

df_mc = df_mc.DefinePerSample("sf", weight_expr)

df_mc = df_mc.Define("eventweight",'EventInfoAuxDyn.mcEventWeights.at(0)')
df_mc = df_mc.Define("puweight",'EventInfoAuxDyn.PileupWeight_NOSYS')
df_mc = df_mc.Define("scalef","sf*eventweight*puweight")

df_mc = df_mc.Define("EventNumber","EventInfoAuxDyn.eventNumber")
df_mc = df_mc.Define("RunNumber","EventInfoAuxDyn.runNumber")

# df_mc = df_mc.Define("bornMass","ComputeBornMass(BornLeptonsAuxDyn.px,\
# BornLeptonsAuxDyn.py,BornLeptonsAuxDyn.pz,\
# BornLeptonsAuxDyn.e,RunNumber)")
# df_mc = df_mc.Filter("bornMass <= 105000","Z overlap")

df_mc = df_mc.Define("good_el_p", "AnalysisElectronsAuxDyn.eta > -2.47 && \
AnalysisElectronsAuxDyn.eta < 2.47 && \
AnalysisElectronsAuxDyn.pt > 7000 && \
AnalysisElectronsAuxDyn.DFCommonElectronsLHLooseBL && \
checkIsolation(AnalysisElectronsAuxDyn.ptcone20_Nonprompt_All_MaxWeightTTVALooseCone_pt500,\
AnalysisElectronsAuxDyn.ptvarcone30_Nonprompt_All_MaxWeightTTVALooseCone_pt500,\
AnalysisElectronsAuxDyn.neflowisol20,\
AnalysisElectronsAuxDyn.pt,0.16) && \
AnalysisElectronsAuxDyn.charge == 1")
df_mc = df_mc.Define("good_el_m", "AnalysisElectronsAuxDyn.eta > -2.47 && \
AnalysisElectronsAuxDyn.eta < 2.47 && \
AnalysisElectronsAuxDyn.pt > 7000 && \
AnalysisElectronsAuxDyn.DFCommonElectronsLHLooseBL && \
checkIsolation(AnalysisElectronsAuxDyn.ptcone20_Nonprompt_All_MaxWeightTTVALooseCone_pt500,\
AnalysisElectronsAuxDyn.ptvarcone30_Nonprompt_All_MaxWeightTTVALooseCone_pt500,\
AnalysisElectronsAuxDyn.neflowisol20,\
AnalysisElectronsAuxDyn.pt,0.16) && \
AnalysisElectronsAuxDyn.charge == -1")

df_mc = df_mc.Define("good_mu_p", "AnalysisMuonsAuxDyn.eta > -2.7 && AnalysisMuonsAuxDyn.eta < 2.7 && AnalysisMuonsAuxDyn.pt > 5000 && AnalysisMuonsAuxDyn.charge == 1")
df_mc = df_mc.Define("good_mu_m", "AnalysisMuonsAuxDyn.eta > -2.7 && AnalysisMuonsAuxDyn.eta < 2.7 && AnalysisMuonsAuxDyn.pt > 5000 && AnalysisMuonsAuxDyn.charge == -1")

df_mc = df_mc.Define("n_el_p", "ROOT::VecOps::Sum(good_el_p)")
df_mc = df_mc.Define("n_el_m", "ROOT::VecOps::Sum(good_el_m)")
df_mc = df_mc.Define("n_mu_p", "ROOT::VecOps::Sum(good_mu_p)")
df_mc = df_mc.Define("n_mu_m", "ROOT::VecOps::Sum(good_mu_m)")

df_mc = df_mc.Define("el_p_pt", "AnalysisElectronsAuxDyn.pt[good_el_p]")
df_mc = df_mc.Define("el_m_pt", "AnalysisElectronsAuxDyn.pt[good_el_m]")
df_mc = df_mc.Define("mu_p_pt", "AnalysisMuonsAuxDyn.pt[good_mu_p]")
df_mc = df_mc.Define("mu_m_pt", "AnalysisMuonsAuxDyn.pt[good_mu_m]")

df_mc = df_mc.Define("el_p_eta", "AnalysisElectronsAuxDyn.eta[good_el_p]")
df_mc = df_mc.Define("el_m_eta", "AnalysisElectronsAuxDyn.eta[good_el_m]")
df_mc = df_mc.Define("mu_p_eta", "AnalysisMuonsAuxDyn.eta[good_mu_p]")
df_mc = df_mc.Define("mu_m_eta", "AnalysisMuonsAuxDyn.eta[good_mu_m]")

df_mc = df_mc.Define("el_p_phi", "AnalysisElectronsAuxDyn.phi[good_el_p]")
df_mc = df_mc.Define("el_m_phi", "AnalysisElectronsAuxDyn.phi[good_el_m]")
df_mc = df_mc.Define("mu_p_phi", "AnalysisMuonsAuxDyn.phi[good_mu_p]")
df_mc = df_mc.Define("mu_m_phi", "AnalysisMuonsAuxDyn.phi[good_mu_m]")

df_mc = df_mc.Filter("(n_el_p >= 1 && n_el_m >= 1) || (n_mu_p >= 1 && n_mu_m >= 1)")
df_mc = df_mc.DefinePerSample("dsid", dsid_expr)

data_path = "../data/"
file_name = "skimmed.root"

df_mc.Snapshot("CollectionTree", data_path + "ttree/" + file_name, {"EventNumber", "RunNumber", "scalef", "dsid", "n_el_p", "n_el_m", "n_mu_p", "n_mu_m",  "el_p_pt", "el_m_pt", "mu_p_pt", "mu_m_pt", "el_p_eta", "el_m_eta", "mu_p_eta", "mu_m_eta", "el_p_phi", "el_m_phi", "mu_p_phi", "mu_m_phi"})



import ROOT
import sys
import argparse

ROOT.gInterpreter.Declare(
    """
float ComputeInvariantMass(float pt1, float eta1, float phi1, float pt2, float eta2, float phi2)
{
    ROOT::Math::PtEtaPhiMVector p1{pt1, eta1, phi1, 0.511};
    ROOT::Math::PtEtaPhiMVector p2{pt2, eta2, phi2, 0.511};
    return 0.001 * (p1 + p2).M();
}
"""
)

parser = argparse.ArgumentParser()
parser.add_argument('--type', type=str, choices=['ttree', 'rntuple'], help='Type of ROOT file')
args = parser.parse_args()

file_type = args.type

input_file = "../data/" + file_type + "/skimmed.root"
output_file = "../data/" + file_type + "/features.root"
df = ROOT.RDataFrame("CollectionTree", input_file)
print(df.GetColumnNames())

df = df.Filter("n_el_p >= 1 && n_el_m >= 1")

df = df.Define("isSig", "dsid == 700493 ? 1 : dsid == 700494 ? 1 : 0 ")

df = df.Define("el_p_1_pt", "el_p_pt[0]")
df = df.Define("el_p_1_eta", "el_p_eta[0]")
df = df.Define("el_p_1_phi", "el_p_phi[0]")
df = df.Define("el_m_1_pt", "el_m_pt[0]")
df = df.Define("el_m_1_eta", "el_m_eta[0]")
df = df.Define("el_m_1_phi", "el_m_phi[0]")
df = df.Define("mee", "ComputeInvariantMass(el_p_1_pt, el_p_1_eta, el_p_1_phi, el_m_1_pt, el_m_1_eta, el_m_1_phi)")

d2 = df.Display({"mee", "RunNumber"}, 10)
d2.Print()

opts_ttree = ROOT.RDF.RSnapshotOptions()
opts_ttree.fOutputFormat =  ROOT.RDF.ESnapshotOutputFormat.kTTree

opts_rntuple = ROOT.RDF.RSnapshotOptions()
opts_rntuple.fOutputFormat =  ROOT.RDF.ESnapshotOutputFormat.kRNTuple

if file_type == "ttree":
    df.Snapshot("CollectionTree", output_file, {"isSig", "mee", "el_p_1_pt", "el_p_1_eta", "el_p_1_phi", "el_m_1_pt", "el_m_1_eta", "el_m_1_phi" }, opts_ttree)

elif file_type == "rntuple":
    df.Snapshot("CollectionTree", output_file, {"isSig", "mee", "el_p_1_pt", "el_p_1_eta", "el_p_1_phi", "el_m_1_pt", "el_m_1_eta", "el_m_1_phi" }, opts_rntuple)


sys.exit()

df_sig = df.Filter("isSig == 1")
df_bkg = df.Filter("isSig == 0")
print("bkg", df_bkg.Count().GetValue())
print("sig", df_sig.Count().GetValue())
print(df.Count().GetValue())

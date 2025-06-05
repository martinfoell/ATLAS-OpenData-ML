// NOTE: The RNTupleImporter class is experimental at this point.
// Functionality and interface are still subject to changes.
 
#include <ROOT/RNTupleDS.hxx>
#include <ROOT/RNTupleImporter.hxx>
#include <ROOT/RNTupleReader.hxx>
#include <ROOT/RPageStorageFile.hxx>
 
#include <TFile.h>
#include <TROOT.h>
#include <TSystem.h>
 
// Import classes from experimental namespace for the time being.
using RNTupleImporter = ROOT::Experimental::RNTupleImporter;
 
// Input and output.
constexpr char const *kTreeFileName = "../data/ttree/skimmed.root";
constexpr char const *kTreeName = "CollectionTree";
constexpr char const *kNTupleFileName = "../data/rntuple/skimmed.root";
 
void skimmed_ttree_to_rntuple()
{
   // RNTupleImporter appends keys to the output file; make sure a second run of the tutorial does not fail
   // with `Key 'Events' already exists in file ntpl008_import.root` by removing the output file.
   gSystem->Unlink(kNTupleFileName);
 
   // Use multiple threads to compress RNTuple data.
   ROOT::EnableImplicitMT();
 
   // Create a new RNTupleImporter object.
   auto importer = RNTupleImporter::Create(kTreeFileName, kTreeName, kNTupleFileName);
 
   // Begin importing.
   importer->Import();
 
   // Inspect the schema of the written RNTuple.
   auto file = std::unique_ptr<TFile>(TFile::Open(kNTupleFileName));
   if (!file || file->IsZombie()) {
      std::cerr << "cannot open " << kNTupleFileName << std::endl;
      return;
   }
   auto ntpl = std::unique_ptr<ROOT::RNTuple>(file->Get<ROOT::RNTuple>("CollectionTree"));
   auto reader = ROOT::RNTupleReader::Open(*ntpl);
   reader->PrintInfo();
 
   // ROOT::RDataFrame df("Events", kNTupleFileName);
   // df.Histo1D({"Jet_pt", "Jet_pt", 100, 0, 0}, "Jet_pt")->DrawCopy();
}

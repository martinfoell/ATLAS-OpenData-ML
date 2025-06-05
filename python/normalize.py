import ROOT
import sys 
import argparse

def NormalizeColumns(df, columns, means, stddevs):
    for col in columns:
        mean = means[col]
        std = stddevs[col]
        if std == 0:
            raise ValueError(f"Standard deviation of column '{col}' is zero. Cannot normalize.")
        
        df = df.Redefine(col, f"({col} - {mean}) / {std}")
        print(f"[INFO] Normalized column: {col} ")
    return df

parser = argparse.ArgumentParser()
parser.add_argument('--type', type=str, choices=['ttree', 'rntuple'], help='Type of ROOT file')
args = parser.parse_args()

file_type = args.type

input_file = "../data/" + file_type + "/features.root"
output_file = "../data/" + file_type + "/normalize.root"

df = ROOT.RDataFrame("CollectionTree", input_file)
print(df.GetColumnNames())


columns = list(df.GetColumnNames())
print("cc", columns)
columns_to_normalize = columns
columns_to_normalize.remove("isSig")

print("Columns to normalize ", columns_to_normalize)

mean = {col: df.Mean(col) for col in columns_to_normalize}
stddev = {col: df.StdDev(col) for col in columns_to_normalize}
    
ROOT.RDF.RunGraphs(list(mean.values()) + list(stddev.values()))

mean_val = {col: mean[col].GetValue() for col in columns_to_normalize}
stddev_val = {col: stddev[col].GetValue() for col in columns_to_normalize}

    
for col, val in mean_val.items():
    print(f"[INFO] Mean of data {col}: {val}")

for col, val in stddev_val.items():
    print(f"[INFO] Stddev of data {col}: {val}")
    

df = NormalizeColumns(df, columns_to_normalize, mean_val, stddev_val)
print(df.GetColumnNames())


opts_ttree = ROOT.RDF.RSnapshotOptions()
opts_ttree.fOutputFormat =  ROOT.RDF.ESnapshotOutputFormat.kTTree

opts_rntuple = ROOT.RDF.RSnapshotOptions()
opts_rntuple.fOutputFormat =  ROOT.RDF.ESnapshotOutputFormat.kRNTuple

if file_type == "ttree":
    df.Snapshot("CollectionTree", output_file, columns, opts_ttree)    

elif file_type == "rntuple":
    df.Snapshot("CollectionTree", output_file, columns, opts_rntuple)    
    

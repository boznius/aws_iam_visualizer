# aws_iam_visualizer
Simple script to visualize and export yaml from IAM relations within AWS 


## How to use the script :

```
# export aws creds or make sure that they are in the session properly

python iam_visualizer.py --generate-graph
Retrieving IAM data...
Writing IAM data to YAML file: iam_data.yaml
Writing IAM data to DOT file: iam_graph.dot
Generating graph visualization...
Graph image generated: iam_graph.png

```

### Other examples : 

```
python iam_visualizer.py --entities=users --name=alice --print-yaml
python iam_visualizer.py --print-yaml
python iam_visualizer.py --print-yaml --generate-graph

```
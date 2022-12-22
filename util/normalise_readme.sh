# This is a utility script for normalising the timestamps in README.md
# It is used during development
# Run from base directory:
# ./util/normalise_readme.sh
sed -i -r 's/[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}/2022-01-01 00:00:00,000/g' README.md
sed -i -r 's/[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}/2022-01-01T00:00:00.000000/g' README.md
sed -i -r 's/_[0-9]{8}-/_20220101-/g' README.md

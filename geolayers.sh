
for FP in data/flexicadastre/geo_layers/*.json; do
    FN=`basename $FP .json`
    OP="$DATA_PATH/flexicadastre/data/shapefiles/$FN"
    mkdir -p $OP
    OF="$OP/$FN.shp"
    ogr2ogr -f "ESRI Shapefile" $OF $FP
    echo $OF;
done;

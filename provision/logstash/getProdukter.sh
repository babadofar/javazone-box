mkdir download
wget  http://www.vinmonopolet.no/api/produkter  -O download/products.csv
iconv -f=ISO-8859-1 -t=UTF-8 download/products.csv > download/iconproducts.csv

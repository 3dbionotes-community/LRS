# LRS

Simple Docker stack for Local Resolution Service

author: [Jose R. Macias](mailto:jr.macias@cnb.csic.es)

(c) Biocomputing Unit ([BCU](http://biocomputingunit.es/)), [CNB-CSIC](http://www.cnb.csic.es/)


INSTALLATION:

DEV
- docker-compose up --build
- docker-compose down

PROD
- docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
- docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

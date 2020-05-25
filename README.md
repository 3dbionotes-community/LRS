# LRS

Simple Docker stack for Local Resolution Service

author: [Jose R. Macias](mailto:jr.macias@cnb.csic.es)

(c) Biocomputing Unit ([BCU](http://biocomputingunit.es/)), [CNB-CSIC](http://www.cnb.csic.es/)

Basic Setup (for development)

** rename sample env-devel files to .env, and provide appropiate values.

Docker stack is handled through regular [docker-compose](https://docs.docker.com/compose/) app life cycle: 
```
docker-compose up
```
If needed, i.e. for installing new dependencies, it can be forecerd to rebuild with:
```
docker-compose up --build
```

There are a couple of volumes shared with the container, one for the [code](./service/tools), another for [data](./service/data).

The tools can be accessed by SSH:
```
ssh ${USER_NAME}@host -p ${SSH_EXT_PORT}
```
or with docker-compose:
```
docker-compose exec tools bash
```


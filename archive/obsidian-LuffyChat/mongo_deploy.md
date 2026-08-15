
```shell
docker run -d --restart=always --name luffy_mongo -p 27017:27017 mongo
```

```shell
docker run -d --restart=always --name mongo_express --link "luffy_mongo:db" -e "ME_CONFIG_MONGODB_URL=mongodb://luffy_mongo:27017/" -p 8081:8081 mongo-express
```

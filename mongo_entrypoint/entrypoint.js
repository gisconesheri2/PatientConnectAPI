
var db = connect(`mongodb://${process.env.MONGO_INITDB_ROOT_USERNAME}:${process.env.MONGO_INITDB_ROOT_PASSWORD}@localhost:27017/admin`);

db = db.getSiblingDB(`${process.env.API_DATABASE}`); // we can not use "use" statement here to switch db

db.createUser(
    {
        user: `${process.env.USERNAME}`,
        pwd: `${process.env.USER_PASSWORD}`,
        roles: [ { role: "readWrite", db: `${process.env.API_DATABASE}`} ],
        passwordDigestor: "server",
    }
)
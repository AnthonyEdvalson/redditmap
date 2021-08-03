const express = require('express')
const app = express()
const sequelize = require('sequelize');
const port = 3000

app.use(express.static('public'));
app.use(express.json());


// Setup for SQLite
const db = new sequelize.Sequelize('sqlite:TEST.db');

const users = db.define("user", {
    name: {
        type: sequelize.DataTypes.STRING,
        primaryKey: true
    },
    mod: {
        type: sequelize.DataTypes.BOOLEAN
    },
    gold: {
        type: sequelize.DataTypes.BOOLEAN
    },
    karma: {
        type: sequelize.DataTypes.INTEGER
    }
}, { tableName: "user", timestamps: false });

const subs = db.define("sub", {
    name: {
        type: sequelize.DataTypes.STRING,
        primaryKey: true
    },
    nsfw: {
        type: sequelize.DataTypes.BOOLEAN
    },
    subscribers: {
        type: sequelize.DataTypes.INTEGER
    }
}, { tableName: "sub", timestamps: false });

const links = db.define("link", {
    user_name: {
        type: sequelize.DataTypes.STRING,   
        primaryKey: true
    },
    sub_name: {
        type: sequelize.DataTypes.STRING,  
        primaryKey: true
    },
    power: {
        type: sequelize.DataTypes.INTEGER
    }
}, { tableName: "link", timestamps: false });


// Endpoint that compiles data from SQLite
app.get('/data', async (req, res) => {
    let allUsers = await users.findAll();
    let allSubs = await subs.findAll();
    let allLinks = await links.findAll();

    let mappedLinks = new Map();
    let subPower = new Map();

    for (let link of allLinks) {
        let uname = link.user_name
        let sname = link.sub_name

        if (!mappedLinks.has(uname))
            mappedLinks.set(uname, []);

        mappedLinks.set(uname, [...mappedLinks.get(uname), link]);

        if (!subPower.has(sname))
            subPower.set(sname, 0);

        subPower.set(sname, subPower.get(sname) + link.power);
    }

    console.log(subPower.get("funny"))

    let nodes = [];
    let nodeId = 0;
    let idMap = new Map();
    let relations = new Map();

    console.log("Processing users...")
    for (let user of allUsers) {
        if (!mappedLinks.has(user.name))
            continue;

        let links = mappedLinks.get(user.name);

        for (let i = 0; i < links.length; i++) {
            for (let j = i + 1; j < links.length; j++) {
                if (links[i].sub_name >= links[j].sub_name)
                    continue;

                let k = links[i].sub_name + ":" + links[j].sub_name;
                let power = links[i].power * links[j].power / 100;

                if (relations.has(k))
                    relations.set(k, [...relations.get(k),  power]);
                else
                    relations.set(k, [power]);
            }
        }
    }

    console.log("Processing subs...")
    for (let sub of allSubs) {
        nodes.push({
            key: nodeId,
            n: sub.name,
            t: 1,
            xxx: sub.nsfw
        });
        idMap.set(sub.name, nodeId);
        nodeId++;
        if (nodeId > 3000)
            break;
    }

    let edges = [];

    console.log("Processing edges...")
    relations.forEach((vs, k) => {
        let [s1, s2] = k.split(":");
        if (!(idMap.has(s1) && idMap.has(s2)))
            return;

        let v = vs.reduce((a, b) => a + b, 0) / (subPower.get(s1) + subPower.get(s2)) * 100
        if (v < 0.15)
            return;

        let s1id = idMap.get(s1);
        let s2id = idMap.get(s2);
        edges.push({
            source: s1id,
            target: s2id,
            s: v
        });
    });
    console.log("Done!")

    res.send({
        nodes,
        links: edges
    });
});

app.listen(port, () => {
  console.log(`Example app listening at http://localhost:${port}`)
});

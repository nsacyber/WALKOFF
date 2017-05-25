#!/usr/bin/env node

fs = require('fs')
path = require('path')

var accountAddrs = process.argv[2]
accountAddrs = accountAddrs.replace(/{/g, "")
accountAddrs = accountAddrs.replace(/}/g, "")

var accountArr = accountAddrs.split('\n')
var allocValue = {}
for (var key in accountArr) {
  allocValue['0x' + accountArr[key]] = {'balance': '99999999000000000000'}
}

var genTemplate = JSON.parse(fs.readFileSync(path.resolve(__dirname, "step2-genesis-template.json"), "utf8"));
genTemplate.alloc = allocValue

fs.writeFileSync(path.resolve(__dirname, "dd/extras/genesis.json"), JSON.stringify(genTemplate, null, 2))

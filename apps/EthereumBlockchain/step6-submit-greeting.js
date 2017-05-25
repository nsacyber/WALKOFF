#!/usr/bin/env node

var fs = require('fs')
var Web3 = require('web3')
var web3 = new Web3()
var contractDeployed = require('./dd/extras/contract-info.js');

var greeting = process.argv[4]
var nodePort = process.argv[2]
var nodeAcc = process.argv[3]
nodeAcc = nodeAcc.replace(/{/g, '')
nodeAcc = nodeAcc.replace(/}/g, '')
var nodeUrl = 'http://localhost:' + nodePort;
web3.setProvider(new web3.providers.HttpProvider(nodeUrl));

var contractAddr = contractDeployed.contractDeployed.address;
var contractAbi = contractDeployed.contractDeployed.abi;
var greeter = web3.eth.contract(contractAbi).at(contractAddr)

console.log(greeter.greet())

greeter.setGreeting.sendTransaction(greeting, {from: nodeAcc, gas: 300000, gasPrice: 0},
  function(error, result) {
    if (error) {
      console.log("Fail to send transaction: " + error);
    } else {
      console.log("Successfully sent transaction with tx hash: " + result);

      var intervalRes = setInterval(function() {
        var txReceipt = web3.eth.getTransactionReceipt(result)
        if (txReceipt != null) {
          console.log(greeter.greet())
          clearInterval(intervalRes);
        } else {
          console.log("Still waiting...")
        }
      }, 10*1000);
    }
  })

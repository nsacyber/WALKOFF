#!/usr/bin/env node

fs = require('fs')
path = require('path')
solc = require('solc')
Web3 = require('web3')
var web3 = new Web3()

var nodePort = process.argv[2]
var nodeAcc = process.argv[3]
nodeAcc = nodeAcc.replace(/{/g, '')
nodeAcc = nodeAcc.replace(/}/g, '')
var nodeUrl = "http://localhost:" + nodePort;
web3.setProvider(new web3.providers.HttpProvider(nodeUrl));

var solFilepath = path.resolve(__dirname, "step5-greeter.sol")
var greeterSol = fs.readFileSync(solFilepath);
var input = {solFilepath : greeterSol.toString()}

var output = solc.compile({sources: input}, 1);
for (var contractName in output.contracts) {
  var greeterCompiled = JSON.parse(output.contracts[contractName].metadata)
  greeterAbi = greeterCompiled["output"]["abi"]
  greeterBin = output.contracts[contractName].bytecode
}
var greeterContract = web3.eth.contract(greeterAbi);

var greeting = "Hello miner!"
var greeter = greeterContract.new(greeting, {
    from: nodeAcc,
    data: "0x" + greeterBin,
    gas: 300000
}, function(error, contract) {
    if (error) {
      console.log("Error creating contract...", error);
    } else {
      if(!contract.address) {
        console.log("Contract transaction send: TransactionHash: " + contract.transactionHash + " waiting to be mined...");
      } else {
        console.log("Contract mined! Address: " + contract.address);
        var contractDeployed = {
          address: contract.address,
          abi: greeterAbi
        };
        fs.writeFileSync(path.resolve(__dirname, "dd/extras/contract-info.js"), "module.exports.contractDeployed = " + JSON.stringify(contractDeployed, null, "  ") + ";");
      }
    }
  });

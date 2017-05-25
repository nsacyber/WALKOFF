pragma solidity ^0.4.11;

contract greeter {
    /* Define variable owner of the type address*/
    address owner;

    /* define variable greeting of the type string */
    string greeting;

    /* this function is executed at initialization and sets the owner of the contract */
    function greeter(string _greeting) public {
      greeting = _greeting;
      owner = msg.sender;
    }

    /* main function */
    function greet() constant returns (string) {
        return greeting;
    }

    /* Update greeting */
    function setGreeting(string newGreeting) {
        greeting = newGreeting;
    }

    /* Function to recover the funds on the contract */
    function kill() {
      if (msg.sender == owner) {
        selfdestruct(owner);
      }
    }
}

# Deploying Other Services

Remember: hendrix treats your web app like just another network resource.

If you need to deploy network resources other than your web app, hendrix is happy to handle them.

For example, the [Cirque project](https://github.com/jMyles/cirque) has a fairly ordinary WSGI frontend, but also connects via UDP to local mesh networking nodes.  This allows users of the WSGI frontend to administer the nodes directly through the local network.

It looks something like this:

```python
reactor = deployer.reactor  # As with the quickstart example, deployer is a HendrixDeploy instance

cjdns_sesh = CirqueCJDNSListener("some_node_IP_address", "the_node_administration_password")

reactor.listenUDP(5500, cjdns_sesh)

deployer.run()
```

Of course, there is additional logic in CirqueCJDNSListener to dictate the traffic to the nodes.  In Twisted terminology, which hendrix mostly uses, CirqueCJDNSListener is a **protocol**.

As you can see, it's easy to use other protocols alongside your web app resource.  You can then share logic and state between them as if they live in the same Python project - because they do!

You can add other protocols to the reactor even after you run the deployer.

Building your own protocols for use in situations like the example above is great, but don't forget about the [dozens of protocols already included in Twisted](http://twistedmatrix.com/documents/current/api/moduleIndex.html).

A far-from-exhaustive list:

* [SOCKS](http://twistedmatrix.com/documents/current/api/twisted.protocols.socks.html)
* [IRC](http://twistedmatrix.com/documents/current/api/twisted.words.protocols.irc.html)
* [IMAP4](http://twistedmatrix.com/documents/current/api/twisted.mail.imap4.html)
* [SSH](http://twistedmatrix.com/documents/current/api/twisted.conch.ssh.transport.html)
* [DNS](http://twistedmatrix.com/documents/current/api/twisted.names.dns.html)

It's as easy to implement any of these as the example above.  You can get started right away on the logic for your IRC-client-built-right-into-a-WSGI-app! :-)

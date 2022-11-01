# Stomp-Client

This repository contains the source for the IOTICS stomp client.

Until the upstream `stomp.py` [next release](https://github.com/jasonrbriggs/stomp.py/blob/0c9d45c6391555d1a462d1ee2cfff95d03aaa871/CHANGELOG.md?plain=1#L6), which contains a websocket implementation, is available, the IOTICS stomp client can be used instead.

Please note that separate gRPC libraries are also available which many users might find more intuitive to use.
In many cases, gRPC is more performant than REST+STOMP as gRPC has been specifically designed with data streaming in mind. See the [IOTICS gRPC documentation](https://docs.iotics.com/docs/iotics-tools#iotics-api-grpc) for more information.

* [iotics-grpc-client-py](https://github.com/Iotic-Labs/iotics-grpc-client-py)
* [iotics-grpc-client-rs](https://github.com/Iotic-Labs/iotics-grpc-client-rs)
* [iotics-grpc-client-ts](https://github.com/Iotic-Labs/iotics-grpc-client-ts)

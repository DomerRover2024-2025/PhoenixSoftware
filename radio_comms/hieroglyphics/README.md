TODO updated as of 1/20:

TODO:
- ~~create scheduler~~
- ~~create message manager on rover side~~
- ~~create weighted round robin~~
- figure out opcode documentation / where everything must go
- ~~~figure out all the metadata that should be associated with a given message.
    - more annoying than it seems; do I need an opcode vs destination?~~~
- actually check the checksums
- rover requesting messages with failed checksums by their ids
    - eg. for one image keep all packets for that image in memory to be requested 
      if a couple of the packets are faulty
- update checksum algorithm
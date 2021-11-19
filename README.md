Links-page
==========

This software unites favorite links from few computers into a single HTTP file.

Installation:
---------

   1. This software will probably run on any Linux that has Python3
   2. Install dependencies:
      `pip3 install -r requirements.txt`
   3. Copy 'example_params.yml' to 'params.yml`
   4. Get credential into a server that supports sftp.
   5. Edit 'params.yml' to reflect the credentials of your host
   6. Create a file 'links_<hostName>.yml'. Look at the example links file.
      This file is composed of topics, sub-topics and URLs.

Operation
---------
   
   1. Edit the 'links_<hostName>.yml' file to add newly found interesting links.
   7. Run 'sync'. This will fetch the 'link_*.yml' files of the other computers and upload your local links file.
   3. View the unified 'links.html' file.

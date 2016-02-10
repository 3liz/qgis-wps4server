wps4server: QGIS Server Plugin to add OGC Web Processing Service capabilities
==============================================================================

Description
---------------

wps4server is a QGIS Server Plugin. It provides OGC Web Processing capabilities. It's based on PyWPS.

For more information, see:
* http://www.opengeospatial.org/standards/wps
* http://pywps.wald.intevation.org

Install on Ubuntu
------------------

Python plugins support for QGIS Server has been introduced with QGIS 2.8 and it is enabled by default on most distributions.

You'll find how to install QGIS Server in the QGIS documentation : http://docs.qgis.org/2.8/en/docs/user_manual/working_with_ogc/ogc_server_support.html

Prerequisites
_______________

We assume that you are working on a fresh install with Apache and FCGI module installed with:

```bash
$ sudo apt-get install apache2 libapache2-mod-fcgid
$ # Enable FCGI daemon apache module
$ sudo a2enmod fcgid
```

Package installation
_____________________

First step is to add debian gis repository, add the following repository:

```bash
$ cat /etc/apt/sources.list.d/debian-gis.list
deb http://qgis.org/debian trusty main
deb-src http://qgis.org/debian trusty main

$ # Add keys
$ sudo gpg --recv-key DD45F6C3
$ sudo gpg --export --armor DD45F6C3 | sudo apt-key add -

$ # Update package list
$ sudo apt-get update && sudo apt-get upgrade
```

Now install qgis server:

```bash
$ sudo apt-get install qgis-server python-qgis
```

Install wps4server plugin
__________________________

```bash
$ sudo mkdir -p /opt/qgis-server/plugins
$ cd /opt/qgis-server/plugins
$ sudo wget https://github.com/3liz/qgis-wps4server/archive/master.zip
$ # In case unzip was not installed before:
$ sudo apt-get install unzip
$ sudo unzip master.zip
$ sudo mv qgis-wps4server-master wps4server
```

Apache virtual host configuration
__________________________________

We are installing the server in a separate virtual host listening on port 81.

Let Apache listen to port 81:

```bash
$ cat /etc/apache2/conf-available/qgis-server-port.conf
Listen 81
$ sudo a2enconf qgis-server-port
```

The virtual host configuration, stored in /etc/apache2/sites-available/001-qgis-server.conf:

```
    <VirtualHost *:81>
        ServerAdmin webmaster@localhost
        DocumentRoot /var/www/html

        ErrorLog ${APACHE_LOG_DIR}/qgis-server-error.log
        CustomLog ${APACHE_LOG_DIR}/qgis-server-access.log combined

        # Longer timeout for WPS... default = 40
        FcgidIOTimeout 120
        FcgidInitialEnv LC_ALL "en_US.UTF-8"
        FcgidInitialEnv PYTHONIOENCODING UTF-8
        FcgidInitialEnv LANG "en_US.UTF-8"
        FcgidInitialEnv QGIS_DEBUG 1
        FcgidInitialEnv QGIS_SERVER_LOG_FILE /tmp/qgis-000.log
        FcgidInitialEnv QGIS_SERVER_LOG_LEVEL 0
        FcgidInitialEnv QGIS_PLUGINPATH "/opt/qgis-server/plugins"

        # ABP: needed for QGIS HelloServer plugin HTTP BASIC auth
        <IfModule mod_fcgid.c>
            RewriteEngine on
            RewriteCond %{HTTP:Authorization} .
            RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]
        </IfModule>

        ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/
        <Directory "/usr/lib/cgi-bin">
            AllowOverride All
            Options +ExecCGI -MultiViews +FollowSymLinks
            Require all granted
            #Allow from all
      </Directory>
    </VirtualHost>
```

Enable the virtual host and restart Apache:

```bash
$ sudo a2ensite 001-qgis-server
$ sudo service apache2 restart
```

Test
_____

Open the link: **http://localhost/qgis_mapserv.fcgi?SERVICE=WPS&REQUEST=GetCapabilities**

Configuration
---------------

wps4server plugin uses an extended PyWPS config file. You will find the default configuration file and an example:
* filters/PyWPS/pywps/default.cfg
* filters/PyWPS/pywps/buffer.cfg

A wps4server configuration file has at least 4 sections:
* **wps** contains general WPS instance settings
* **provider** contains information about you, your organization and so on
* **server** contains server settings, constraints, safety configuration and so on
* **qgis** contains specific QGIS settings

The **qgis** section contains:
* **qgisserveraddress** for accessing output data as a service
* **processing_folder** the directory to find models, scripts and rscripts; the default path is ~/.qgis2/processing
* **providers** the processes provider list to publish through WPS; by default all processes providers are published; you can select in this list *qgis,gdalogr,script,model,r,grass,grass70,saga,otb*
* **algs_filter** a string to filter processes based on name and title
* **algs** a list of processes to publish; for example *qgis:fixeddistancebuffer,qgis:delaunaytriangulation,qgis:concavehull*
* **input_bbox_crss** a list of available input bounding box CRSs
* **output_ows_crss** a list of available CRSs for Opengis Web Service output
* **outputs_minetypes_vector** a list of available output mimeTypes for vector, this parameter is made for reducing the list and select the default one
* **outputs_minetypes_raster** a list of available output mimeTypes for raster, this parameter is made for reducing the list and select the default one

To use an other config file than the default one, you can use:
* **CONFIG** parameter in the URL
* **PYWPS_CFG** environmental param

Use default data
------------------

wps4server is able to use server geodata, which datasource is defined in a QGIS project files. The project can be the same that you use for WMS, WFS or WCS.

To use a QGIS project, you can use:
* **MAP** parameter in the URL, like for the others OGC Web Services
* **QGIS_PROJECT_FILE** environmental param

# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para verseriesynovelas
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import re

from core import config
from core import logger
from core import scrapertools
from core import servertools
from core.item import Item


# Configuracion del canal
__modo_grafico__ = config.get_setting('modo_grafico', 'verseriesynovelas')
__perfil__ = int(config.get_setting('perfil', 'verseriesynovelas'))

# Fijar perfil de color            
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E'],
          ['0xFF58D3F7', '0xFF2E9AFE', '0xFF2E64FE']]
color1, color2, color3 = perfil[__perfil__]

DEBUG = config.get_setting("debug")
CHANNEL_HOST = "http://www.verseriesynovelas.tv"
CHANNEL_HEADERS = [
    ["User-Agent", "Mozilla/5.0"],
    ["Accept-Encoding", "gzip, deflate"],
    ["Referer", CHANNEL_HOST]
    ]


def login():
    logger.info("pelisalacarta.channels.verseriesynovelas login")

    try:
        user = config.get_setting("verseriesynovelasuser", "verseriesynovelas")
        password = config.get_setting("verseriesynovelaspassword", "verseriesynovelas")
        if user == "" and password == "":
            return False, "Para ver los enlaces de este canal es necesario registrarse en www.verseriesynovelas.tv"
        elif user == "" or password == "":
            return False, "Usuario o contraseña en blanco. Revisa tus credenciales"
        data = scrapertools.downloadpage("http://www.verseriesynovelas.tv/")
        if user in data:
            return True, ""
        
        try:
            os.remove(os.path.join(config.get_data_path(), 'cookies', 'verseriesynovelas.tv.dat'))
        except:
            pass

        post = "log=%s&pwd=%s&redirect_to=http://www.verseriesynovelas.tv/wp-admin/&action=login" % (user, password)
        data = scrapertools.downloadpage("http://www.verseriesynovelas.tv/iniciar-sesion", post=post)
        if "La contraseña que has introducido" in data:
            logger.info("pelisalacarta.channels.verseriesynovelas Error en el login")
            return False, "Contraseña errónea. Comprueba tus credenciales"
        elif "Nombre de usuario no válido" in data:
            logger.info("pelisalacarta.channels.verseriesynovelas Error en el login")
            return False, "Nombre de usuario no válido. Comprueba tus credenciales"            
        else:
            logger.info("pelisalacarta.channels.verseriesynovelas Login correcto")
            return True, ""
    except:
        import traceback
        logger.info(traceback.format_exc())
        return False, "Error durante el login. Comprueba tus credenciales"


def mainlist(item):
    logger.info("pelisalacarta.channels.verseriesynovelas mainlist")
    itemlist = []
    item.text_color = color1
    
    logueado, error_message = login()
    
    if not logueado:
        itemlist.append(item.clone(title=error_message, action="", text_color="darkorange"))
    else:
        itemlist.append(item.clone(title="Nuevos Capítulos", action="novedades", fanart="http://i.imgur.com/9loVksV.png",
                                   url="http://www.verseriesynovelas.tv/archivos/nuevo"))
        itemlist.append(item.clone(title="Últimas Series", action="ultimas", fanart="http://i.imgur.com/9loVksV.png",
                                   url="http://www.verseriesynovelas.tv/"))
        itemlist.append(item.clone(title="Lista de Series A-Z", action="indices", fanart="http://i.imgur.com/9loVksV.png",
                                   url="http://www.verseriesynovelas.tv/"))
        itemlist.append(item.clone(title="Categorías", action="indices", fanart="http://i.imgur.com/9loVksV.png",
                                   url="http://www.verseriesynovelas.tv/"))
        itemlist.append(item.clone(title="", action=""))
        itemlist.append(item.clone(title="Buscar...", action="search", fanart="http://i.imgur.com/9loVksV.png"))
    itemlist.append(item.clone(title="Configurar canal...", action="configuracion", text_color="gold", folder=False))
    
    return itemlist


def configuracion(item):
    from platformcode import platformtools
    platformtools.show_channel_settings()
    if config.is_xbmc():
        import xbmc
        xbmc.executebuiltin("Container.Refresh")


def indices(item):
    logger.info("pelisalacarta.channels.verseriesynovelas indices")

    itemlist = []
    data = scrapertools.downloadpage(item.url, headers=CHANNEL_HEADERS)
    data = data.replace("\n", "").replace("\t", "")

    if "Categorías" in item.title:
        bloque = scrapertools.find_single_match(data, '<span>Seleccion tu categoria</span>(.*?)</section>')
        matches = scrapertools.find_multiple_matches(bloque, '<li.*?<a href="([^"]+)">(.*?)</a>')
        for url, title in matches:
            itemlist.append(item.clone(action="ultimas", title=title, url=url))
    else:
        bloque = scrapertools.find_single_match(data, '<ul class="alfabetico">(.*?)</ul>')
        matches = scrapertools.find_multiple_matches(bloque, '<li.*?<a href="([^"]+)".*?>(.*?)</a>')
        for url, title in matches:
            itemlist.append(item.clone(action="ultimas", title=title, url=url))

    return itemlist


def search(item, texto):
    logger.info("pelisalacarta.channels.verseriesynovelas search")
    item.url = "http://www.verseriesynovelas.tv/archivos/h1/?s=" + texto
    if "Buscar..." in item.title:
        return ultimas(item, texto)
    else:
        try:
            return busqueda(item, texto)
        except:
            import sys
            for line in sys.exc_info():
                logger.error("%s" % line)
            return []


def busqueda(item, texto=""):
    logger.info("pelisalacarta.channels.verseriesynovelas busqueda")
    itemlist = []
    item.text_color = color2

    data = scrapertools.downloadpage(item.url, headers=CHANNEL_HEADERS)
    data = data.replace("\n", "").replace("\t", "")

    bloque = scrapertools.find_single_match(data, '<ul class="list-paginacion">(.*?)</section>')
    bloque = scrapertools.find_multiple_matches(bloque, '<li><a href=(.*?)</li>')
    for match in bloque:
        patron = '([^"]+)".*?<img class="fade" src="([^"]+)".*?<h2>(.*?)</h2>'
        matches = scrapertools.find_multiple_matches(match, patron)
        for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
            # fix para el buscador para que no muestre entradas con texto que no es correcto
            if texto.lower() not in scrapedtitle.lower():
                continue

            scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).replace(" online", "")
            titleinfo = re.sub(r'(?i)((primera|segunda|tercera|cuarta|quinta|sexta) temporada)', "Temporada",
                               scrapedtitle)
            titleinfo = titleinfo.split("Temporada")[0].strip()
            titleinfo = re.sub(r'(\(\d{4}\))|(\(\d{4}\s*-\s*\d{4}\))', '', titleinfo)

            if DEBUG:
                logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
            itemlist.append(item.clone(action="episodios", title=scrapedtitle, url=scrapedurl,
                                       thumbnail=scrapedthumbnail, fulltitle=scrapedtitle, show=titleinfo,
                                       contentType="tvshow", contentTitle=titleinfo))
    # Paginación
    next_page = scrapertools.find_single_match(data, '<a class="nextpostslink".*?href="([^"]+)">')
    if next_page != "":
        itemlist.append(item.clone(title=">> Siguiente", url=next_page))

    return itemlist


def newest(categoria):
    logger.info("pelisalacarta.channels.verseriesynovelas newest")
    itemlist = []
    item = Item()
    try:
        if categoria == 'series':
            item.channel = "verseriesynovelas"
            item.extra = "newest"
            item.url = "http://www.verseriesynovelas.tv/archivos/nuevo"
            itemlist = novedades(item)

            if itemlist[-1].action == "novedades":
                itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def novedades(item):
    logger.info("pelisalacarta.channels.verseriesynovelas novedades")
    itemlist = []
    item.text_color = color2

    data = scrapertools.downloadpage(item.url, headers=CHANNEL_HEADERS)
    data = data.replace("\n", "").replace("\t", "")

    bloque = scrapertools.find_single_match(data, '<section class="list-galeria">(.*?)</section>')
    bloque = scrapertools.find_multiple_matches(bloque, '<li><a href=(.*?)</a></li>')
    for match in bloque:
        patron = '([^"]+)".*?<img class="fade" src="([^"]+)".*?title="(?:ver |)([^"]+)"'
        matches = scrapertools.find_multiple_matches(match, patron)
        for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
            titleinfo = scrapertools.decodeHtmlentities(scrapedtitle)
            try:
                titleinfo = re.split("Temporada", titleinfo, flags=re.IGNORECASE)[0]
            except:
                try:
                    titleinfo = re.split("Capitulo", titleinfo, flags=re.IGNORECASE)[0]
                except:
                    pass
            scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle) + " "
            if item.extra != "newest":
                contentTitle = titleinfo
            else:
                contentTitle = re.sub(r'(?i)(temporada |episodios |capítulo |capitulo )', '', scrapedtitle)

            if "ES.png" in match:
                scrapedtitle += "[CAST]"
            if "SUB.png" in match:
                scrapedtitle += "[VOSE]"
            if "LA.png" in match:
                scrapedtitle += "[LAT]"
            if "EN.png" in match:
                scrapedtitle += "[V.O]"
            if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
            itemlist.append(item.clone(action="findvideos", title=scrapedtitle, url=scrapedurl,
                                       thumbnail=scrapedthumbnail, fulltitle=titleinfo, show=titleinfo,
                                       contentTitle=contentTitle, context=["buscar_trailer"], contentType="tvshow"))

    if item.extra != "newest":
        try:
            from core import tmdb
            tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
        except:
            pass
        
    #Paginación
    next_page = scrapertools.find_single_match(data, '<a class="nextpostslink".*?href="([^"]+)">')
    if next_page != "":
        itemlist.append(item.clone(title=">> Siguiente", url=next_page, text_color=color3))

    return itemlist


def ultimas(item, texto=""):
    logger.info("pelisalacarta.channels.verseriesynovelas ultimas")
    itemlist = []
    item.text_color = color2

    data = scrapertools.downloadpage(item.url, headers=CHANNEL_HEADERS)
    data = data.replace("\n", "").replace("\t", "")

    bloque = scrapertools.find_single_match(data, '<ul class="list-paginacion">(.*?)</section>')
    bloque = scrapertools.find_multiple_matches(bloque, '<li><a href=(.*?)</li>')
    for match in bloque:
        patron = '([^"]+)".*?<img class="fade" src="([^"]+)".*?<h2>(.*?)</h2>'
        matches = scrapertools.find_multiple_matches(match, patron)
        for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
            # fix para el buscador para que no muestre entradas con texto que no es correcto
            if texto.lower() not in scrapedtitle.lower():
                continue

            scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).replace(" online", "")
            titleinfo = re.sub(r'(?i)((primera|segunda|tercera|cuarta|quinta|sexta) temporada)', "Temporada",
                               scrapedtitle)
            titleinfo = titleinfo.split("Temporada")[0].strip()
            titleinfo = re.sub(r'(\(\d{4}\))|(\(\d{4}\s*-\s*\d{4}\))', '', titleinfo)

            if DEBUG:
                logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
            itemlist.append(item.clone(action="episodios", title=scrapedtitle, url=scrapedurl,
                                       thumbnail=scrapedthumbnail, fulltitle=titleinfo,
                                       contentTitle=titleinfo, context=["buscar_trailer"], show=titleinfo,
                                       contentType="tvshow"))

    try:
        from core import tmdb
        tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    except:
        pass

    # Paginación
    next_page = scrapertools.find_single_match(data, '<a class="nextpostslink".*?href="([^"]+)">')
    if next_page != "":
        itemlist.append(item.clone(title=">> Siguiente", url=next_page, text_color=color3))

    return itemlist


def episodios(item):
    logger.info("pelisalacarta.channels.verseriesynovelas episodios")
    itemlist = []

    data = scrapertools.downloadpage(item.url, headers=CHANNEL_HEADERS)
    data = data.replace("\n", "").replace("\t", "")

    plot = scrapertools.find_single_match(data, '<p><p>(.*?)</p>')
    item.plot = scrapertools.htmlclean(plot)
    bloque = scrapertools.find_multiple_matches(data, '<td data-th="Temporada"(.*?)</div>')
    for match in bloque:
        matches = scrapertools.find_multiple_matches(match, '.*?href="([^"]+)".*?title="([^"]+)"')
        for scrapedurl, scrapedtitle in matches:
            try:
                season, episode = scrapertools.find_single_match(scrapedtitle, '(\d+)(?:×|x)(\d+)')
                item.infoLabels['season'] = season
                item.infoLabels['episode'] = episode
                contentType = "episode"
            except:
                try:
                    episode = scrapertools.find_single_match(scrapedtitle, '(?i)(?:Capitulo|Capítulo|Episodio)\s*(\d+)')
                    item.infoLabels['season'] = "1"
                    item.infoLabels['episode'] = episode
                    contentType = "episode"
                except:
                    contentType = "tvshow"
               
            scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle) + "  "
            scrapedtitle = scrapedtitle.replace('Temporada', '')
            if "ES.png" in match:
                scrapedtitle += "[CAST]"
            if "SUB.png" in match:
                scrapedtitle += "[VOSE]"
            if "LA.png" in match:
                scrapedtitle += "[LAT]"
            if "EN.png" in match:
                scrapedtitle += "[V.O]"
            if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"]")
            itemlist.append(item.clone(action="findvideos", title=scrapedtitle, url=scrapedurl,
                                       fulltitle=scrapedtitle, contentType=contentType))

    itemlist.reverse()
    if itemlist and item.extra != "episodios":
        try:
            from core import tmdb
            tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
        except:
            pass
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                                   text_color="magenta"))
        if item.category != "" and config.get_library_support():
            itemlist.append(Item(channel=item.channel, title="Añadir esta temporada a la biblioteca", url=item.url,
                                 action="add_serie_to_library", extra="episodios", text_color="green", show=item.show))

    return itemlist


def findvideos(item):
    logger.info("pelisalacarta.channels.verseriesynovelas findvideos")
    itemlist = []
    item.text_color = color3

    if item.extra == "newest" and item.extra != "episodios":
        try:
            from core import tmdb
            tmdb.set_infoLabels_item(item, __modo_grafico__)
        except:
            pass

    data = scrapertools.downloadpage(item.url, headers=CHANNEL_HEADERS)
    if "valida el captcha" in data:
        logueado, error = login()
        data = scrapertools.downloadpage(item.url, headers=CHANNEL_HEADERS)    
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)

    bloque = scrapertools.find_multiple_matches(data, '<tr><td data-th="Idioma">(.*?)</div>')
    for match in bloque:
        patron = 'data-th="Calidad">(.*?)<.*?' \
                 '"Servidor".*?src="http://www.google.com/s2/favicons\?domain=(.*?)\.' \
                 '.*?<td data-th="Enlace"><a href="(http://www.verseriesynovelas.tv/link/enlaces.php.*?)"'
        matches = scrapertools.find_multiple_matches(match, patron)
        for quality, server, url in matches:
            if server == "streamin":
                server = "streaminto"
            if server== "waaw":
                server = "netutv"
            if server == "ul":
                server = "uploadedto"
            try:
                servers_module = __import__("servers."+server)
                title = "Ver vídeo en "+server+"  ["+quality+"]"
                if "Español.png" in match:
                    title += " [CAST]"
                if "VOS.png" in match:
                    title += " [VOSE]"
                if "Latino.png" in match:
                    title += " [LAT]"
                if "VO.png" in match:
                    title += " [V.O]"
                itemlist.append(item.clone(action="play", title=title, url=url))
            except:
                pass

    if not itemlist: 
        itemlist.append(item.clone(action="", title="No se ha encontrado ningún enlace"))
    if item.extra != "episodios":
        url_lista = scrapertools.find_single_match(data, '<a class="regresar" href="([^"]+)"')
        if url_lista != "":
            itemlist.append(item.clone(action="episodios", title="Ir a la Lista de Capítulos", url=url_lista,
                                       text_color="red", context=""))

    return itemlist


def play(item):
    logger.info("pelisalacarta.channels.verseriesynovelas play")
    itemlist = []
    
    try:
        data = scrapertools.downloadpage(item.url, headers=CHANNEL_HEADERS)
    except:
        pass

    url_redirect = scrapertools.find_single_match(data, 'href="(http://www.verseriesynovelas.tv/link/enlace.php\?u=[^"]+)"')
    if not url_redirect:
        try:
            import StringIO
            compressedstream = StringIO.StringIO(data)
            import gzip
            gzipper = gzip.GzipFile(fileobj=compressedstream)
            data = gzipper.read()
            gzipper.close()
            url_redirect = scrapertools.find_single_match(data, 'href="(http://www.verseriesynovelas.tv/link/enlace.php\?u=[^"]+)"')
        except:
            pass

    
    location = scrapertools.get_header_from_response(url_redirect, headers=CHANNEL_HEADERS[:2], header_to_get="location")
    enlaces = servertools.findvideos(data=location)
    if len(enlaces) > 0:
        itemlist.append(item.clone(action="play", server=enlaces[0][2], url=enlaces[0][1]))

    return itemlist

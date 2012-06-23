from django.conf.urls import patterns, include, url
from followthestory import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
                       (r'^search-form/$',views.search_form),
                       (r'^search/$',views.search),
                       (r'^search/result.png$',views.plot_graph),
                       (r'^search/twitterchart.png$',views.plot_twittergraph),
    # Examples:
    # url(r'^$', 'followthestory.views.home', name='home'),
    # url(r'^followthestory/', include('followthestory.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

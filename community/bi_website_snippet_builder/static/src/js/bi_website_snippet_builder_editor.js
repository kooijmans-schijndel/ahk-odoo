odoo.define('bi_website_snippet_builder.snippet_builder', function (require) {
'use strict';

    var core = require('web.core');
    var ajax = require('web.ajax');
    var weContext = require('web_editor.context');
    var options = require('web_editor.snippets.options');
    var utils = require('website.utils');
    var _t = core._t;

    var Dialog = require('web.Dialog');

    var snippet_builder_common = options.Class.extend({
        select_snippet_list: function (previewMode, value) {
            var self = this;
            var def = self.$target;

            var $content = '<form class="snippet_form" action="/make/snippet"><div class="form-group"><label for="name">Name:</label><input type="name" class="form-control snippet_name" id="name"/></div><div class="card"><div class="card-header"><ul id="codeTabs" class="nav nav-tabs card-header-tabs" role="tablist"><li class="nav-item"><a class="nav-link active" id="nav_tabs_link_1599807340974_3" data-toggle="tab" href="#nav_tabs_content_1599807340974_3" role="tab" aria-controls="nav_tabs_content_1599807340974_3" aria-selected="true" data-original-title="" title="" aria-describedby="tooltip854641" contenteditable="true">HTML</a></li><li class="nav-item"><a class="nav-link" id="nav_tabs_link_1599807340974_4" data-toggle="tab" href="#nav_tabs_content_1599807340974_4" role="tab" aria-controls="nav_tabs_content_1599807340974_4" aria-selected="false" data-original-title="" title="" aria-describedby="tooltip395646">CSS</a></li><li class="nav-item"><a class="nav-link" id="nav_tabs_link_1599807340974_5" data-toggle="tab" href="#nav_tabs_content_1599807340974_5" role="tab" aria-controls="nav_tabs_content_1599807340974_5" aria-selected="false" data-original-title="" title="" aria-describedby="tooltip479076">JS</a></li></ul></div><div id="codeTabsContent" class="card-body tab-content"><div class="tab-pane fade active show" id="nav_tabs_content_1599807340974_3" role="tabpanel" aria-labelledby="nav_tabs_link_1599807340974_3"><label for="html">HTML Code:</label><textarea class="form-control html_code" name="html" rows="15" id="html_code"></textarea></div><div class="tab-pane fade" id="nav_tabs_content_1599807340974_4" role="tabpanel" aria-labelledby="nav_tabs_link_1599807340974_4"><label for="css">CSS Code:</label><textarea class="form-control css_code" name="css" rows="15" id="css_code"></textarea></div><div class="tab-pane fade" id="nav_tabs_content_1599807340974_5" role="tabpanel" aria-labelledby="nav_tabs_link_1599807340974_5"><label for="js">JS Code:</label><textarea class="form-control js_code" name="js" rows="15" id="js_code"></textarea></div></div></div></form>'

            var dialog = new Dialog(this, {
                size: 'medium',
                title: _t('Snippet Builder'),
                $content: _t($content),
                buttons: [
                    {text: _t("Make snippet"), classes: 'btn-primary make_snippet', click: this._onClickMakeSnippet.bind(this)},
                    {text: _t("Close"),classes: 'btn-primary close_model', close: true}
                ],
            }).open();

            var resolver, rejecter;
            var def = new Promise(function (resolve, reject){
                resolver = resolve;
                rejecter = reject;
            });
            return def;
        },
        _onClickMakeSnippet: function () {
            var form = this.$target.parents("body").find('.snippet_form');
            var name = form.find(".snippet_name").val();
            var html_code = form.find(".html_code").val();
            var css_code = form.find(".css_code").val();
            var js_code = form.find(".js_code").val();
            var main_snippet = this.$target;
            if(name !== null && name !== '' && html_code !== null && html_code !== '') {
                ajax.jsonRpc('/make/snippet', 'call',{'name':name,'html_code':html_code,'css_code':css_code,'js_code':js_code}).then(function(data) {
                    main_snippet.append(data);
                    form.parents().find(".close_model").click();
                });
            }else{
                form.parents().find(".make_snippet").before("<span class='text-danger w-100 mb16'>Name and HTML Code is required</span>");
            }
        },
        onBuilt: function () {
            var self = this;
            this._super();
            this.select_snippet_list('click').guardedCatch(function (reason) {
                self.getParent()._onRemoveClick($.Event( "click" ));
            });
        },
    });
    options.registry.build_snippet = snippet_builder_common.extend({
        cleanForSave: function () {
            return this._super.apply(this, arguments);
        },
    });
});

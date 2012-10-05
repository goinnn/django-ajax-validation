(function($) {
    function inputs(form)   {
        return form.find(":input:visible:not(:button)");
    }

    var errorRemover = {
    p: function(form, fields){
        get_form_error_position(form, '__all__').prev('ul.errorlist').remove();
        if (!fields)
            form.find('ul.errorlist').remove();
        else
            fields.closest('p').prev('ul.errorlist').remove();
    },
    table: function(form, fields){
        form.find('tr:has(ul.errorlist):not(:has(label))').remove();
        if (!fields)
            inputs(form).prev('ul.errorlist').remove();
        else
            fields.prev('ul.errorlist').remove();

    },
    ul: function(form, fields){
        form.find('li:has(ul.errorlist):not(:has(label))').remove();
        if (!fields)
            inputs(form).prev().prev('ul.errorlist').remove();
        else
            fields.prev().prev('ul.errorlist').remove();
    },
    };

    function removeErrors(form, form_type, fields){
        if (fields)
            fields = $(fields.map(function(n){ return '*[name="'+n+'"]'; }).join(', '));
       return errorRemover[form_type](form, fields);
    }


    function get_form_error_position(form, key) {
        key = key || '__all__';
        if (key == '__all__') {
            var filter = ':first';
        } else {
            var filter = ':first[id^=id_' + key.replace('__all__', '') + ']';
        }
        return inputs(form).filter(filter).parent();
    };

    var errorInjector = {
    p: function(form, data) {
            $.each(data.errors, function(key, val) {
                if (key.indexOf('__all__') >= 0) {
                    var error = get_form_error_position(form, key);
                    if (error.prev().is('ul.errorlist')) {
                        error.prev().before('<ul class="errorlist"><li>' + val + '</li></ul>');
                    } else {
                        error.before('<ul class="errorlist"><li>' + val + '</li></ul>');
                    }
                } else {
                    $('#' + key, form).parent().before('<ul class="errorlist"><li>' + val + '</li></ul>');
                }
            });
        },
    table: function(form, data) {
            $.each(data.errors, function(key, val) {
                if (key.indexOf('__all__') >= 0) {
                    get_form_error_position(form, key).parent().before('<tr><td colspan="2"><ul class="errorlist"><li>' + val + '</li></ul></td></tr>');
                } else {
                    $('#' + key, form).before('<ul class="errorlist"><li>' + val + '</li></ul>');
                }
            });
        },
    ul: function(form, data)  {
            $.each(data.errors, function(key, val) {
                if (key.indexOf('__all__') >= 0) {
                    get_form_error_position(form, key).before('<li><ul class="errorlist"><li>' + val + '</li></ul></li>');
                } else {
                    $('#' + key, form).prev().before('<ul class="errorlist"><li>' + val + '</li></ul>');
                }
            });
        },
    };

    function injectErrors(type, form, data){
    errorInjector[type](form, data);
    }

    function getUntilCurrent(ev, nodeNames) {
        var current = ev.originalEvent.explicitOriginalTarget;
        if (current.nodeName.toLowerCase() === "option") {
            current = $(current).parents("select")[0];
        }
         if (nodeNames.split(", ").indexOf(current.nodeName.toLowerCase()) === -1) {
            return false;
        }
        return current;
    }

    $.fn.validate = function(url, settings) {
        settings = $.extend({
            type: 'table',
            callback: false,
            fields: false,
            dom: this,
            event: 'submit',
            submitHandler: null,
            untilCurrent: false,
            removeErrors: removeErrors,
            injectErrors: injectErrors,
            getUntilCurrent: getUntilCurrent
        }, settings);

        return this.each(function() {
            var form = $(this);
            var current = null;
            settings.dom.bind(settings.event, function(ev)  {
                var status = false;
                var responseData = {};
                var data = form.serialize();
                var nodeNames = "input, select, textarea";
                if (settings.fields) {
                    data += '&' + $.param({fields: settings.fields});
                } else if (settings.untilCurrent) {
                    current = settings.getUntilCurrent(ev, nodeNames);
                    if (!current) {
                        return current;
                    }
                    var f = $(current).parents("form");
                    var find = false;
                    var fieldsName = []
                    var fields = f.find(nodeNames).each(function () {
                        if (!find) {
                            fieldsName[fieldsName.length] = $(this).attr("name");
                        } 
                        if (this === current) {
                            find = true;
                            return;
                        }
                    });
                    data += '&' + $.param({fields: fieldsName});
                }
                var that = this;
                $.ajax({
                    async: false,
                    data: data,
                    dataType: 'json',
                    traditional: true,
                    error: function(XHR, textStatus, errorThrown)   {
                        status = true;
                    },
                    success: function(data, textStatus) {
                        responseData = data;
                        status = data.valid;
                        var fields = settings.fields;
                        var fieldsTags = $(that).find(nodeNames);
                        var fieldsToRemove = [];
                        if (current !== null) {
                            for (var i=0; i<fieldsTags.length; i++) {
                                var field = fieldsTags[i];
                                if (fields !== null || fields.indexOf(f) != -1) {
                                    fieldsToRemove[fieldsToRemove.length] = field.name;
                                }
                                if (field == current) {
                                    break;
                                }
                            }
                        } else {
                            fieldsToRemove = fields;
                        }
                        console.log(fieldsToRemove);
                        settings.removeErrors(form, settings.type, fieldsToRemove);
                        if (!status)    {
                            if (settings.callback)  {
                                settings.callback(data, form);
                            } else {
                                settings.injectErrors(settings.type, form, data);
                            }
                        }
                    },
                    type: 'POST',
                    url: url
                });
                if (status && settings.submitHandler) {
                    return settings.submitHandler(form, responseData);
                }
                return status;
            });
        });
    };
})(jQuery);


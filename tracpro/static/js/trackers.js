function formsetFor(ruleType) {
    $('.rule-formset').formset({
        addText: '+ add another ' + ruleType + ' rule',
        addCssClass: 'rule-formset-add btn btn-primary',
        deleteText: '',
        deleteCssClass: 'glyphicon glyphicon-trash'
    });
}

export default {
    template: '#moonscan-component',
    data: function () {
        return {
            moonscan_text: '',
            moonscan_result: []
        };
    },
    mounted: function () {
        this.$refs.scan_text.focus();
    },
    watch: {

    },
    methods: {
        onPaste: function() {
            this.moonscan_result = parseMoonScan(this.moonscan_text);
            console.log(this.moonscan_result);
        },
        addMoonDetail: function() {

            var token = this.$root.$data.token;
            var header = this.$root.$data.header;
            var ajaxHeaders = {};
            ajaxHeaders[header] = token;

            $.ajax({
                cache: false,
                type: 'POST',
                url: "SaveMoonDetail",
                data: JSON.stringify(this.moonscan_result),
                contentType: 'application/json; charset=UTF-8',
                processData: false,
                dataType: "json",
                headers: ajaxHeaders
            }).done(function (data) {

                if (data.success) {


                    if (self.$toast != null) {

                        self.$toast.success('Scans updated succesfully!', {
                            position: 'bottom'
                        });
                    }

                    self.$emit('scan-added');
                }
                else {
                    self.showError = true;
                    self.errors = data.messages;
                }

            });


        }
    }
}

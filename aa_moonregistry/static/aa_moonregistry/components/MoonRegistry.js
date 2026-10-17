export default {
    template: '#moon-component',
    data: function () {
        return {
            sort: { property: "moon_name", direction: "asc" },
            selUniverse: [],
            rarityOptions: [4, 8, 16, 32, 64],
            raritySelection: '',
            selRarity: [],
            selOres: [],
            selSovOwners: [],
            efficiency: '0.90628105568',
            efficiencyError: false,
            moons: [],
            moons_flag: [], 
            next_cursor: '',
            show_modal: false,
            is_loading: false,
            requestId: 0
        };
    },
    props: ['refresh_key'],
    mounted: function () {
        this.loadData();
    },
    watch: {
        sort: {
            deep: true,
            handler: function () {
                this.applySort();
            }
        },
        refresh_key: function () {
            if(!this.is_loading)
                this.loadData();
        }
    },
    methods: {
        loadData: function () {

            var me = this;

            var universe = _.map(this.selUniverse, 'id').join(',')
            var rarity = this.selRarity.join(',')
            var oreTypeIds = _.map(this.selOres, 'id').join(',');
            var sovOwnerIds = _.map(this.selSovOwners, 'id').join(',');

            // empty is first load, null is no more
            if(this.next_cursor != null)
            {
                this.is_loading = true
                var requestId = ++this.requestId;
                var efficiency = String(this.efficiency == null ? '' : this.efficiency).trim();

                var url = 'MoonList?' + $.param({
                    universe: universe,
                    rarity: rarity,
                    ore_type_id: oreTypeIds,
                    sov_owner_id: sovOwnerIds,
                    sort: this.sort.property,
                    dir: this.sort.direction,
                    cursor: this.next_cursor,
                    efficiency: efficiency
                });

                $.get(url, function (data) {
                    if (requestId !== me.requestId) return;

                    me.is_loading = false;

                    me.next_cursor = data.next_cursor;

                    _.each(data.items, function (item) {
                        me.moons.push(item);
                        me.moons_flag.push({ val: false });
                    });
                }).fail(function () {
                    if (requestId === me.requestId) me.is_loading = false;
                });
            }
        },
        efficiencyChanged: function () {
            var value = String(this.efficiency == null ? '' : this.efficiency).trim();
            this.efficiencyError = value === '' || !Number.isFinite(Number(value)) || Number(value) < 0 || Number(value) > 1;
            this.requestId++;
            this.moons = [];
            this.moons_flag = [];
            this.next_cursor = this.efficiencyError ? null : '';
            this.is_loading = false;
            if (!this.efficiencyError) this.loadData();
        },
        universeSelected: function(item) {
            if(item && item.id) {
                var index = _.findIndex(this.selUniverse, function (t) { return t.id === item.id; });

                if(index === -1) {
                    this.selUniverse.push(item);
                    this.moons = [];
                    this.next_cursor = '';
                    this.loadData();
                }
            }
        },
        raritySelected: function() {
            var rarity = Number(this.raritySelection);

            if(rarity && this.selRarity.indexOf(rarity) === -1) {
                this.selRarity.push(rarity);
                this.moons = [];
                this.next_cursor = '';
                this.loadData();
            }

            this.raritySelection = '';
        },
        oreSelected: function(item) {
            if(item && item.id) {
                var typeId = Number(item.id);
                var index = _.findIndex(this.selOres, function (ore) { return ore.id === typeId; });

                if(index === -1) {
                    this.selOres.push({
                        id: typeId,
                        name: item.name
                    });
                    this.moons = [];
                    this.next_cursor = '';
                    this.loadData();
                }
            }
        },
        sovOwnerSelected: function(item) {
            if (item && item.id) {
                var ownerId = Number(item.id);
                var index = _.findIndex(this.selSovOwners, function (owner) { return owner.id === ownerId; });

                if (index === -1) {
                    this.selSovOwners.push({ id: ownerId, name: item.filter_name || item.name, fullName: item.name });
                    this.moons = [];
                    this.moons_flag = [];
                    this.next_cursor = '';
                    this.loadData();
                }
            }
        },
        removeUniverseInput: function(id) {
            var index = _.findIndex(this.selUniverse, function (t) { return t.id === id; });
            if(index > -1) {
                this.selUniverse.splice(index, 1)
                this.moons = [];
                this.next_cursor = '';
                this.loadData();
            }
        },
        removeRarityInput: function(rarity) {
            var index = this.selRarity.indexOf(rarity);
            if(index > -1) {
                this.selRarity.splice(index, 1);
                this.moons = [];
                this.next_cursor = '';
                this.loadData();
            }
        },
        removeOreInput: function(typeId) {
            var index = _.findIndex(this.selOres, function (ore) { return ore.id === typeId; });
            if(index > -1) {
                this.selOres.splice(index, 1);
                this.moons = [];
                this.next_cursor = '';
                this.loadData();
            }
        },
        removeSovOwnerInput: function(ownerId) {
            var index = _.findIndex(this.selSovOwners, function (owner) { return owner.id === ownerId; });
            if (index > -1) {
                this.selSovOwners.splice(index, 1);
                this.moons = [];
                this.moons_flag = [];
                this.next_cursor = '';
                this.loadData();
            }
        },
        addScan: function() {
            this.show_modal = true;
            console.log('add scan');
        },
        closeModal: function() {
            this.show_modal = false
        },
        
        formatDate: function (date) {
            if (date != null)
                return moment.utc(date).format('YYYY-MM-DD HH:mm');
            else
                return '';
        },
        formatFloat: function (number) {
            return numeral(number).format('0.0')
        },          
        addCommas: function (num) {
            if(num)
                return numeral(num).format('0,0');
            else
                return num;
        },
        metProfitability: function (moon) {
            if(moon.met_thirty_day_price == null || moon.met_thirty_day_cost == null)
                return null;

            return Number(moon.met_thirty_day_price) - Number(moon.met_thirty_day_cost);
        },
        isSortProp: function (prop) {
            return (this.sort.property == prop);
        },
        showSortIcon: function (prop, dir) {
            return (this.sort.property == prop && this.sort.direction == dir);
        },
        toggleSort: function (prop) {
            if (this.sort.property == prop) {
                if (this.sort.direction == 'asc')
                    this.sort.direction = 'desc';
                else
                    this.sort.direction = 'asc';
            }
            else // switching properties so set and set to default asc
            {
                this.sort.property = prop;
                this.sort.direction = 'asc';
            }
        },
        toggleChild: function (index) {
            this.moons_flag[index].val = !this.moons_flag[index].val;
        },
        applySort: function () {
            // reset page
            this.next_cursor = '';
            this.moons = []
            this.loadData();
        }
    }
}















// class Chart{
//   constructor(type,xdata,ydata){
//     this.type=type;
//     this.xdata=xdata;
//     this.ydata=ydata;
    
//   }
// }

const labels = {{ labels | tojson}};

const data = {
    labels: labels,
    datasets: [{
        label: 'Users',
        backgroundColor: 'rgb(255, 99, 132)',
        borderColor: 'rgb(255, 99, 132)',
        data: {{ data | tojson}},
    }]
};

const config = {
    type: 'bar',
    data: data,
    options: { maintainAspectRatio: false }
};

const myChart = new Chart(
    document.getElementById('myChart'),
    config
);
const fs = require('fs')

async function main(profileName) {
    console.log('Create read stream')
    console.log(parseInt(process.argv[2]))
    var s = fs.createReadStream(null, {fd: parseInt(process.argv[2])});

    s.on('data', function(data) {
        console.log(data.toString())
    });

    s.on('end', function() {
        console.log('Finished');
    });

    // This catches any errors that happen while creating the readable stream (usually invalid names)
    s.on('error', function(err) {
        console.log(err)
    });
    console.log('complete')
}

if (require.main === module) {
    main()
}

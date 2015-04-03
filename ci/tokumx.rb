require './ci/common'

def tokumx_version
  ENV['FLAVOR_VERSION'] || '2.0.1'
end

def tokumx_rootdir
  "#{ENV['INTEGRATIONS_DIR']}/tokumx_#{tokumx_version}"
end

namespace :ci do
  namespace :tokumx do |flavor|
    task :before_install => ['ci:common:before_install']

    task :install => ['ci:common:install'] do
      unless Dir.exist? File.expand_path(tokumx_rootdir)
        # Downloads
        # http://www.tokutek.com/tokumx-for-mongodb/download-community/
        sh %(curl -s -L\
             -o $VOLATILE_DIR/tokumx-#{tokumx_version}.tgz\
             https://s3.amazonaws.com/dd-agent-tarball-mirror/tokumx-#{tokumx_version}-linux-x86_64-main.tar.gz)
        sh %(mkdir -p #{tokumx_rootdir})
        sh %(tar zxf $VOLATILE_DIR/tokumx-#{tokumx_version}.tgz\
             -C #{tokumx_rootdir} --strip-components=1)
      end
      exit 0
    end

    task :before_script => ['ci:common:before_script'] do
      sh %(mkdir -p $VOLATILE_DIR/tokumxd1)
      sh %(mkdir -p $VOLATILE_DIR/tokumxd2)
      hostname = `hostname`.strip
      sh %(#{tokumx_rootdir}/bin/tokumxd --port 37017\
           --pidfilepath $VOLATILE_DIR/tokumxd1/tokumx.pid\
           --dbpath $VOLATILE_DIR/tokumxd1\
           --replSet rs0/#{hostname}:37018\
           --logpath $VOLATILE_DIR/tokumxd1/tokumx.log\
           --noprealloc --rest --fork)
      sh %(#{tokumx_rootdir}/bin/tokumxd --port 37018\
          --pidfilepath $VOLATILE_DIR/tokumxd2/tokumx.pid\
          --dbpath $VOLATILE_DIR/tokumxd2\
          --replSet rs0/#{hostname}:37017\
          --logpath $VOLATILE_DIR/tokumxd2/tokumx.log\
          --noprealloc --rest --fork)

      # Set up the replica set + print some debug info
      sleep_for 15
      sh %(#{tokumx_rootdir}/bin/tokumx\
           --eval "printjson(db.serverStatus())" 'localhost:37017'\
           >> $VOLATILE_DIR/tokumx.log)
      sh %(#{tokumx_rootdir}/bin/tokumx\
           --eval "printjson(db.serverStatus())" 'localhost:37018'\
           >> $VOLATILE_DIR/tokumx.log)
      sh %(#{tokumx_rootdir}/bin/tokumx\
           --eval "printjson(rs.initiate()); printjson(rs.conf());" 'localhost:37017'\
           \>> $VOLATILE_DIR/tokumx.log)
      sleep_for 30
      sh %(#{tokumx_rootdir}/bin/tokumx\
           --eval "printjson(rs.config()); printjson(rs.status());" 'localhost:37017'\
           >> $VOLATILE_DIR/tokumx.log)
      sh %(#{tokumx_rootdir}/bin/tokumx\
           --eval "printjson(rs.config()); printjson(rs.status());" 'localhost:37018'\
            >> $VOLATILE_DIR/tokumx.log)
    end

    task :script => ['ci:common:script'] do
      this_provides = [
        'tokumx'
      ]
      Rake::Task['ci:common:run_tests'].invoke(this_provides)
    end

    task :before_cache => ['ci:common:before_cache']

    task :cache => ['ci:common:cache']

    task :cleanup => ['ci:common:cleanup'] do
      sh %(kill `cat $VOLATILE_DIR/tokumxd1/tokumx.pid` `cat $VOLATILE_DIR/tokumxd2/tokumx.pid`)
    end

    task :execute do
      exception = nil
      begin
        %w(before_install install before_script script).each do |t|
          Rake::Task["#{flavor.scope.path}:#{t}"].invoke
        end
      rescue => e
        exception = e
        puts "Failed task: #{e.class} #{e.message}".red
      end
      if ENV['SKIP_CLEANUP']
        puts 'Skipping cleanup, disposable environments are great'.yellow
      else
        puts 'Cleaning up'
        Rake::Task["#{flavor.scope.path}:cleanup"].invoke
      end
      if ENV['TRAVIS']
        %w(before_cache cache).each do |t|
          Rake::Task["#{flavor.scope.path}:#{t}"].invoke
        end
      end
      fail exception if exception
    end
  end
end

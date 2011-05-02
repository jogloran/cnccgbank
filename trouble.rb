#! /usr/bin/env ruby
phases = ARGV.empty? ? %w{tagged binarised labelled fixed_rc fixed_adverbs fixed_np} : ARGV

STDIN.each_with_index {|line, i|
    if i != 0 and i % 10 == 0
        STDOUT.write "Continue? "
        case gets
        when "n"
            exit
        end
    end
        
    line.chomp!
    
    (line =~ /(\d+):(\d+)\((\d+)\)/) || (line =~ /(\d+),(\d+),(\d+)/) || (line =~ /(\d+).*(\d+).*(\d+)/)
    doc_name = "chtb_%02d%02d.fid" % [$1, $2]
    pdf_name = "wsj_%02d%02d.%02d.pdf" % [$1, $2, $3]
    section_name = "%02d" % $1
    
    puts "Making %d:%d(%d)..." % [$1, $2, $3]
    `./make_all.sh #{doc_name}:#{$3}`
    phases.each {|phase|
        if ["tagged", "binarised"].include? phase
            `./t -q -D #{phase}_dots #{phase}/#{doc_name}:#{$3} 2>&1`
        else
            `./t -q -D #{phase}_dots -R PrefacedPTBReader #{phase}/#{doc_name}:#{$3} 2>&1`
        end
    }
    open_cmd = "open -a /Applications/Preview.app "
    dot_files = phases.map {|phase| "#{phase}_dots/#{section_name}/#{pdf_name}"}.select {|file| test ?f, file}
    open_cmd += dot_files.join(' ')
    system open_cmd
}
